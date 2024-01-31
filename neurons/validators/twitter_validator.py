
import math
import torch
import wandb
import random
import json
import bittensor as bt
from base_validator import AbstractNeuron
from template.protocol import TwitterScraperStreaming, TwitterPromptAnalysisResult
from reward import (
    RewardModelType,
    RewardScoringType
)
from typing import List
from utils.mock import MockRewardModel
import time
from neurons.validators.penalty import (
    TaskValidationPenaltyModel,
    AccuracyPenaltyModel,
    LinkValidationPenaltyModel
)
from reward.prompt import PromptRewardModel, init_tokenizer
from neurons.validators.utils.tasks import TwitterTask
from template.dataset import  MockTwitterQuestionsDataset
from template.services.twitter import TwitterAPIClient
from template import QUERY_MINERS
import asyncio

class TwitterScraperValidator:
    def __init__(self, neuron: AbstractNeuron):
        self.streaming = True
        self.query_type = "text"
        self.model = "gpt-4-1106-preview"
        self.weight = 1
        self.seed = 1234
        self.neuron = neuron
        self.timeout=120

        # Init device.
        bt.logging.debug("loading", "device")
        bt.logging.debug("self.neuron.config.neuron.device = ", str(self.neuron.config.neuron.device))

        self.reward_weights = torch.tensor(
            [
                self.neuron.config.reward.prompt_based_weight,
                # self.neuron.config.reward.prompt_summary_links_content_based_weight,
            ],
            dtype=torch.float32,
        ).to(self.neuron.config.neuron.device)


        if self.reward_weights.sum() != 1:
            message = (
                f"Reward function weights do not sum to 1 (Current sum: {self.reward_weights.sum()}.)"
                f"Check your reward config file at `reward/config.py` or ensure that all your cli reward flags sum to 1."
            )
            bt.logging.error(message)
            raise Exception(message)
    
        tokenizer = None
        model = None
        if (self.neuron.config.reward.prompt_based_weight > 0 or \
           self.neuron.config.reward.prompt_summary_links_content_based_weight > 0) and \
           not self.neuron.config.neuron.is_disable_tokenizer_reward:
            tokenizer, model = init_tokenizer(self.neuron.config.neuron.device)
           
        self.reward_functions = [ 
            PromptRewardModel(device=self.neuron.config.neuron.device, 
                              scoring_type=RewardScoringType.twitter_question_answer_score,
                              tokenizer=tokenizer,
                              model=model,
                              is_disable_tokenizer_reward=self.neuron.config.neuron.is_disable_tokenizer_reward
                              )
            if self.neuron.config.reward.prompt_based_weight > 0
            else MockRewardModel(RewardModelType.prompt.value),              
        ]

        self.penalty_functions = [
            # TaskValidationPenaltyModel(max_penalty=0.6),
            LinkValidationPenaltyModel(max_penalty=0.9),
            # AccuracyPenaltyModel(max_penalty=1),
        ]
        self.twitter_api = TwitterAPIClient()

    async def process_single_response(self, resp, prompt):
        default = TwitterScraperStreaming(messages=prompt, model=self.model, seed=self.seed)
        full_response = ""
        synapse_object = None

        try:
            async for chunk in resp:
                if isinstance(chunk, str):
                    full_response += chunk
                elif isinstance(chunk, bt.Synapse):
                    if chunk.is_failure:
                        raise Exception("Dendrite's status code indicates failure")
                    synapse_object = chunk
        except Exception as e:
            bt.logging.trace(f"Process Single Response: {e}")
            return default

        if synapse_object is not None:
            return synapse_object

        return default
        
    async def process_async_responses(self, async_responses, prompt):
        # Create a list of coroutine objects for each response
        tasks = [self.process_single_response(resp, prompt) for resp in async_responses]
        # Use asyncio.gather to run them concurrently
        responses = await asyncio.gather(*tasks)
        return responses
    
    async def return_tokens(self, chunks):
        async for resp in chunks:
            if isinstance(resp, str):
                try:
                    chunk_data = json.loads(resp)
                    tokens = chunk_data.get("tokens", "")
                    bt.logging.trace(tokens)
                    yield tokens
                except json.JSONDecodeError:
                    bt.logging.trace(f"Failed to decode JSON chunk: {resp}")

    async def run_task_and_score(self, task: TwitterTask, strategy=QUERY_MINERS.RANDOM, is_only_allowed_miner=True, is_intro_text= False, specified_uids=None):
        task_name = task.task_name
        prompt = task.compose_prompt()

        bt.logging.debug("run_task", task_name)

        # Record event start time.
        event = {"name": task_name, "task_type": task.task_type}
        start_time = time.time()
        
        # Get random id on that step
        uids = await self.neuron.get_uids(strategy=strategy, 
                                          is_only_allowed_miner=is_only_allowed_miner,
                                          specified_uids=specified_uids)
        
        axons = [self.neuron.metagraph.axons[uid] for uid in uids]
        synapse = TwitterScraperStreaming(messages=prompt, model=self.model, seed=self.seed, is_intro_text=is_intro_text)

        # Make calls to the network with the prompt.
        async_responses = await self.neuron.dendrite.forward(
            axons=axons,
            synapse=synapse,
            timeout=self.timeout,
            streaming=self.streaming,
            deserialize=False,
        )

        return async_responses, uids, event, start_time
    
    def process_content_links(self, responses):
        try:
            for response in responses:
                if self.neuron.config.neuron.disable_twitter_links_content_fetch:
                    com_links = self.twitter_api.find_twitter_links(response.completion)
                    response.links_content = com_links
                    response.tweets = com_links
                else:
                    time.sleep(10)
                    completion = response.completion
                    bt.logging.trace(
                        f"process_content_links completion: {completion}"
                    )
                    twitter_links = self.twitter_api.find_twitter_links(completion)
                    bt.logging.trace(
                        f"process_content_links twitter_links: {twitter_links}"
                    )
                    if len(twitter_links) > 0:
                        json_response = self.twitter_api.fetch_twitter_data_for_links(twitter_links)
                        bt.logging.trace(
                            f"process_content_links fetch_twitter_data_for_links: {json_response}"
                        )
                        if 'data' in json_response:
                            links_content =  json_response['data']
                            response.links_content = links_content
                        elif 'errors' in json_response:
                            errors = json_response['errors']
                            bt.logging.info(f"Process cotent links: {errors}")
        except Exception as e:
            bt.logging.error(f"Error in process_content_links: {e}")
            return

    async def compute_rewards_and_penalties(self, event, prompt, task, responses, uids, start_time):
        try:
            bt.logging.info("Computing rewards and penalties")

            self.process_content_links(responses)

            rewards = torch.zeros(len(responses), dtype=torch.float32).to(self.neuron.config.neuron.device)
            for weight_i, reward_fn_i in zip(self.reward_weights, self.reward_functions):
                reward_i_normalized, reward_event = reward_fn_i.apply(task.base_text, responses, task.task_name)
                rewards += weight_i * reward_i_normalized.to(self.neuron.config.neuron.device)
                if not self.neuron.config.neuron.disable_log_rewards:
                    event = {**event, **reward_event}
                bt.logging.trace(str(reward_fn_i.name), reward_i_normalized.tolist())
                bt.logging.info(f"Applied reward function: {reward_fn_i.name} with reward: {reward_event.get(reward_fn_i.name, 'N/A')}")
                

            for penalty_fn_i in self.penalty_functions:
                raw_penalty_i, adjusted_penalty_i, applied_penalty_i = penalty_fn_i.apply_penalties(responses, task)
                rewards *= applied_penalty_i.to(self.neuron.config.neuron.device)
                if not self.neuron.config.neuron.disable_log_rewards:
                    event[penalty_fn_i.name + "_raw"] = raw_penalty_i.tolist()
                    event[penalty_fn_i.name + "_adjusted"] = adjusted_penalty_i.tolist()
                    event[penalty_fn_i.name + "_applied"] = applied_penalty_i.tolist()
                bt.logging.trace(str(penalty_fn_i.name), applied_penalty_i.tolist())
                bt.logging.info(f"Applied penalty function: {penalty_fn_i.name} with reward: {adjusted_penalty_i.tolist()}")

            scattered_rewards = self.neuron.update_moving_averaged_scores(uids, rewards)
            self.log_event(task, event, start_time, uids, rewards, prompt=task.compose_prompt())

            scores = torch.zeros(len(self.neuron.metagraph.hotkeys))
            uid_scores_dict = {}
            wandb_data = {
                "modality": "twitter_scrapper",
                "prompts": {},
                "responses": {},
                "scores": {},
                "timestamps": {},
            }
            bt.logging.info(f"======================== Reward ===========================")
            for uid_tensor, reward, response in zip(uids, rewards.tolist(), responses):
                uid = uid_tensor.item()
                completion_length = len(response.completion) if response.completion is not None else 0
                links_content_length = len(response.links_content) if response.links_content is not None else 0
                tweets_length = len(response.tweets) if response.tweets is not None else 0
                bt.logging.info(f"uid: {uid};  score: {reward};  completion length: {completion_length};  links_content length: {links_content_length}; tweets length: {tweets_length};")
            bt.logging.info(f"======================== Reward ===========================")

            for uid_tensor, reward, response in zip(uids, rewards.tolist(), responses):
                uid = uid_tensor.item()  # Convert tensor to int
                uid_scores_dict[uid] = reward
                scores[uid] = reward  # Now 'uid' is an int, which is a valid key type
                wandb_data["scores"][uid] = reward
                wandb_data["responses"][uid] = response.completion
                wandb_data["prompts"][uid] = prompt

            await self.neuron.update_scores(wandb_data)

            return rewards
        except Exception as e:
            bt.logging.error(f"Error in compute_rewards_and_penalties: {e}")
            raise e
        
    def log_event(self, task, event, start_time, uids, rewards, prompt):
        def log_event(event):
            for key, value in event.items():
                bt.logging.debug(f"{key}: {value}")
        event.update({
            "step_length": time.time() - start_time,
            "prompt": prompt,
            "uids": uids.tolist(),
            "rewards": rewards.tolist(),
            "propmt": task.base_text
        })
        bt.logging.debug("Run Task event:", str(event))
        # log_event(event)
    
    async def query_and_score(self, strategy=QUERY_MINERS.RANDOM):
        try:
            dataset = MockTwitterQuestionsDataset()
            prompt = dataset.next()

            task_name = "augment"
            task = TwitterTask(base_text=prompt, task_name=task_name, task_type="twitter_scraper", criteria=[])

            async_responses, uids, event, start_time = await self.run_task_and_score(
                task=task,
                strategy=strategy,
                is_only_allowed_miner=False
            )
        
            responses = await self.process_async_responses(async_responses, prompt)
            await self.compute_rewards_and_penalties(event=event, 
                                                    prompt=prompt,
                                                    task=task, 
                                                    responses=responses, 
                                                    uids=uids, 
                                                    start_time=start_time)     
        except Exception as e:
            bt.logging.error(f"Error in query_and_score: {e}")
            raise e
        
    async def organic(self, query):
        try:
            prompt = query['content']        
            task_name = "augment"
            task = TwitterTask(base_text=prompt, task_name=task_name, task_type="twitter_scraper", criteria=[])

            async_responses, uids, event, start_time = await self.run_task_and_score(
                task=task,
                strategy=QUERY_MINERS.RANDOM,
                is_only_allowed_miner=True,
                is_intro_text=True,
            )

            responses = []
            for resp in async_responses:
                try:
                    full_response = ""
                    try:
                        async for chunk in resp:
                            if isinstance(chunk, str):
                                full_response += chunk
                                yield chunk
                            elif isinstance(chunk, bt.Synapse):
                                if chunk.is_failure:
                                    raise Exception("Dendrite's status code indicates failure")
                                synapse_object = chunk

                    except Exception as e:
                        bt.logging.trace(f"Organic Async Response: {e}")
                        responses.append(TwitterScraperStreaming(messages=prompt, model=self.model, seed=self.seed))
                        continue

                    if synapse_object is not None:
                        responses.append(synapse_object)
                        

                except Exception as e:
                    bt.logging.trace(f"Error for resp in async_responses: {e}")
                    responses.append(TwitterScraperStreaming(messages=prompt, model=self.model, seed=self.seed))

            async def process_and_score_responses():
                await self.compute_rewards_and_penalties(event=event,
                                                        prompt=prompt, 
                                                        task=task, 
                                                        responses=responses, 
                                                        uids=uids, 
                                                        start_time=start_time)    
            asyncio.create_task(process_and_score_responses())
        except Exception as e:
            bt.logging.error(f"Error in organic: {e}")
            raise e


    async def organic_specified(self, query, specified_uids=None):
        try:
            prompt = query['content']      

            task_name = "augment"
            task = TwitterTask(base_text=prompt, task_name=task_name, task_type="twitter_scraper", criteria=[])

            yield f"Contacting miner IDs: {'; '.join(map(str, specified_uids))} \n\n\n"
            async_responses, uids, event, start_time = await self.run_task_and_score(
                task=task,
                strategy=QUERY_MINERS.ALL,
                is_only_allowed_miner=False,
                specified_uids=specified_uids
            )
        
            responses = await self.process_async_responses(async_responses, prompt)
            rewards = await self.compute_rewards_and_penalties(event=event, 
                                                    prompt=prompt,
                                                    task=task, 
                                                    responses=responses, 
                                                    uids=uids, 
                                                    start_time=start_time) 
            for uid_tensor, reward, response in zip(uids, rewards.tolist(), responses):
                yield f"Miner ID: {uid_tensor.item()} - Reward: {reward:.2f}\n\n"
                yield "----------------------------------------\n\n"
                yield f"Miner's Completion Output:\n{response.completion}\n\n"
                yield "========================================\n\n"

            missing_uids = set(specified_uids) - set(uid.item() for uid in uids)
            for missing_uid in missing_uids:
                yield f"No response from Miner ID: {missing_uid}\n"
                yield "----------------------------------------\n\n\n"

        except Exception as e:
            bt.logging.error(f"Error in query_and_score: {e}")
            raise e