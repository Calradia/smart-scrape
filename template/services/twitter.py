import requests
import os
import json
import asyncio
import re
import random
from datetime import datetime
from template.utils import call_openai
from template.protocol import TwitterPromptAnalysisResult
import bittensor as bt
from typing import List, Dict, Any
from urllib.parse import urlparse
from template.dataset import MockTwitterQuestionsDataset
from template.llm import LLMManger

BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')

VALID_DOMAINS = ["twitter.com", "x.com"]
twitter_api_query_example = {
    'query': '(from:twitterdev -is:retweet) OR #twitterdev',
    'tweet.fields': "",
    'user.fields': "id,name,username",
    # 'start_time' : 'YYYY-MM-DDTHH:mm:ssZ', #todo need filter start and end time if need from prompt
    # 'end_time': 'YYYY-MM-DDTHH:mm:ssZ',
    'max_results': '2',
    'media.fields': "",
    # 'since_id': "Returns results with a Tweet ID greater than (that is, more recent than) the specified ID. The ID specified is exclusive and responses will not include it.",
    # 'unit_id': "Returns results with a Tweet ID less than (that is, older than) the specified ID. The ID specified is exclusive and responses will not include it."s
}

query_examples = [
    'pepsi OR cola OR "coca cola"',
    '("Twitter API" OR #v2) -"recent search"',
    'thankunext #fanart OR @arianagrande',

    'to:twitterdev OR to:twitterapi -to:twitter',
    'from:TwitterDev url:"https://t.co"',
    'retweets_of:twitterdev OR retweets_of:twitterapi',
    'place_country:US OR place_country:MX OR place_country:CA',
    'data @twitterdev -is:retweet',
    '"mobile games" -is:nullcast',
    'from:twitterdev -has:hashtags',
    'from:twitterdev announcement has:links',
    '#meme has:images',
    ': #icebucketchallenge has:video_link',
    'recommend #paris has:geo -bakery',
    'recommend #paris lang:en',
    '(kittens OR puppies) has:media',
    '#nowplaying has:mentions',
    '#stonks has:cashtags',
    '#nowplaying is:verified',
    'place:"new york city" OR place:seattle OR place:fd70c22040963ac7',
    'conversation_id:1334987486343299072 (from:twitterdev OR from:twitterapi)',
    'context:domain_id.entity_id',
    'has:media',
    'has:links OR is:retweet',
    '"twitter data" has:mentions (has:media OR has:links)',
    '(grumpy cat) OR (#meme has:images)',
    'skiing -snow -day -noschool',
    '(happy OR happiness) place_country:GB -birthday -is:retweet',
    '(happy OR happiness) lang:en -birthday -is:retweet',
    '(happy OR happiness OR excited OR elated) lang:en -birthday -is:retweet -holidays',
    'has:geo (from:NWSNHC OR from:NHC_Atlantic OR from:NWSHouston OR from:NWSSanAntonio OR from:USGS_TexasRain OR from:USGS_TexasFlood OR from:JeffLindner1) -is:retweet'
]

bad_query_examples = [
    '(OpenAI OR GPT-3) (#OpenAI OR #ArtificialIntelligence)',
    '(horrible OR worst OR sucks OR bad OR disappointing) (place_country:US OR place_country:MX OR place_country:CA)'

]

# - media.fields allowed values: "duration_ms,height,media_key,preview_image_url,type,url,width"
# - max_results only between 10 - 100
# - user.fields only allowed: "created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,url,username,verified,withheld"
# - tweet.fields only allowed: "attachments,author_id,context_annotations,conversation_id,created_at,entities,geo,id,in_reply_to_user_id,lang,possibly_sensitive,referenced_tweets,reply_settings,source,text,withheld,edit_history_tweet_ids"

def get_query_gen_prompt(prompt, is_accuracy=True):
    accuracy_text = ""
    if is_accuracy:
        accuracy_text = f"""   
        RULES:
            1. Accurately generate keywords, hashtags, and mentions based solely on text that is unequivocally relevant to the user's prompt and after generate Twitter API query
        """
    else:
        accuracy_text = f"""   
        RULES:
            1. Similiar Generate keywords, hashtags, and mentions that are closely related to the user's prompt and after generate Twitter API query
        """
    content = f"""
        Given the specific User's prompt: '{prompt}', please perform the following tasks and provide the results in a JSON object format:

        1. Identify and list the key keywords which is related to User's prompt.
        2. Determine and list relevant hashtags which is related to User's prompt.
        3. Identify and list any significant user mentions frequently associated with User's prompt, but don't create if users has not mentioned any user
        4. Generate Twitter API query params based on examples and your knowledge below, user keywords, mentions, hashtags for query which is related to User's Prompt.

        {accuracy_text}

        Twitter API Params: "{twitter_api_query_example}"
        Twitter API Params.query right work: "{query_examples}"
        Twitter API Params.query does not work: {bad_query_examples}
        Twitter API Params rules:
            - If a query.word consists of two or more words, enclose them in quotation marks, i.e "Coca cola"
            - Don't use "since:" and "until:" for date filter
            - end_time must be on or after start_date
            - use lang filter in query, and filter based on user's language, default lang.en
            - media.fields allowed values: "preview_image_url,type,url,width"
            - max_results only between 10 - 100
            - user.fields only allowed: "created_at,description,id,location,name,profile_image_url,url,username,verified"
            - tweet.fields only allowed: "author_id,created_at,id,possibly_sensitive,text"


        Output example:
        {{
            "keywords": ["list of identified keywords based on the prompt"],
            "hashtags": ["#relevantHashtag1", "..."],
            "user_mentions": ["@significantUser1", "..."],
            "api_params": {{
                "query": "constructed query based on keywords, hashtags, and user mentions",
                "tweet.fields": "all important fields needed to answer user's prompt",
                "user.fields": "relevant user fields",
                "max_results": "appropriate number based on user's prompt"
            }}
        }}"
    """
    bt.logging.trace("get_query_gen_prompt Start   ============================")
    bt.logging.trace(content)
    bt.logging.trace("get_query_gen_prompt End   ==============================")
    return content

def get_fix_query_prompt(prompt, old_query, error, is_accuracy= True):
    task = get_query_gen_prompt(prompt=prompt, is_accuracy=is_accuracy)
        
    old_query_text = ""
    if old_query:
        old_query_text = f"""Your previous query was: 
        <OLD_QUERY>
        {old_query}
        </OLD_QUERY>
        which did not return any results, Please analyse it and make better query."""
    content = F"""That was task for you: 
    <TASK>
    {task}
    <Task>,
    That was user's promot: 
    <PROMPT>
    {prompt}
    </PROMPT>

    {old_query_text}

    That was Twitter API's result: "{error}"

    Please, make a new better Output to get better result from Twitter API.
    Output must be as Output example as described in <TASK>.
    """
    return content

class TwitterAPIClient:
    def __init__(self, 
                 llm_manager = None,
                 query_model = 'gpt-3.5-turbo-1106',
                 fix_query_model = 'gpt-4-1106-preview',
                 ):
        # self.bearer_token = os.environ.get("BEARER_TOKEN")
        self.bearer_token = BEARER_TOKEN
        self.twitter_link_regex = re.compile(
            r'https?://(?:' + '|'.join(re.escape(domain) for domain in VALID_DOMAINS) +
            r')/[\w/:%#\$&\?\(\)~\.=\+\-]+(?<![\.\)])', re.IGNORECASE)
        self.query_model = query_model
        self.fix_query_model = fix_query_model
        self.llm = llm_manager if llm_manager else LLMManger()

    def bearer_oauth(self, r):
        """
        Method required by bearer token authentication.
        """
        r.headers["Authorization"] = f"Bearer {self.bearer_token}"
        r.headers["User-Agent"] = "v2RecentSearchPython"
        return r

    def connect_to_endpoint(self, url, params):
        response = requests.get(url, auth=self.bearer_oauth, params=params)

        if response.status_code in [401, 403]:
            bt.logging.error(f"Critical Twitter API Ruquest error occurred: {response.text}")
            os._exit(1)

        return response

    def get_tweet_by_id(self, tweet_id):
        tweet_url = f"https://api.twitter.com/2/tweets/{tweet_id}"
        response = self.connect_to_endpoint(tweet_url, {})
        if response.status_code != 200:
            return None
        return response.json()

    
    def get_tweets_by_ids(self, tweet_ids):
        ids = ','.join(tweet_ids)  # Combine all tweet IDs into a comma-separated string
        tweets_url = f"https://api.twitter.com/2/tweets?ids={ids}"
        response = self.connect_to_endpoint(tweets_url, {})
        if response.status_code != 200:
            return []
        return response.json()

    def get_recent_tweets(self, query_params):
        search_url = "https://api.twitter.com/2/tweets/search/recent"
        response = self.connect_to_endpoint(search_url, query_params)
        return response
    
    async def generate_query_params_from_prompt(self, prompt, is_accuracy = True):
        """
        This function utilizes OpenAI's API to analyze the user's query and extract relevant information such 
        as keywords, hashtags, and user mentions.
        """
        content  = get_query_gen_prompt(prompt, is_accuracy)
        messages = [{'role': 'user', 'content': content }]
        bt.logging.trace(content)
        res = await self.llm.prompt(messages=messages,
                        temperature=0.2,
                        model=self.query_model,
                        response_format={"type": "json_object"})
        # res = await call_openai(messages=messages, 
        #                         temperature=0.2, 
        #                         model=self.query_model, 
        #                         seed=None, 
        #                         response_format={"type": "json_object"})
        response_dict = json.loads(res)
        bt.logging.trace("generate_query_params_from_prompt Content: ", response_dict)
        return response_dict

    async def fix_twitter_query(self, prompt, query, error, is_accuracy = True):
        """
        This method refines the user's initial query by leveraging OpenAI's API 
        to parse and enhance the query with more precise keywords, hashtags, and user mentions, 
        aiming to improve the search results from the Twitter API.
        """
        try:
            content  = get_fix_query_prompt(prompt=prompt,
                                            old_query=query,
                                            error=error,
                                            is_accuracy=is_accuracy)
            messages = [{'role': 'user', 'content': content }]
            bt.logging.trace(content)
            res = await self.llm.prompt(messages=messages,
                temperature=0.5,
                model=self.fix_query_model,
                response_format={"type": "json_object"})
            # res = await call_openai(messages=messages, 
            #                         temperature=0.5, 
            #                         model=self.fix_query_model, 
            #                         seed=None, 
            #                         response_format={"type": "json_object"})
            response_dict = json.loads(res)
            bt.logging.trace("fix_twitter_query Content: ", response_dict)
            return response_dict
        except Exception as e:
            bt.logging.info(e)
            return [], None

    async def analyse_prompt_and_fetch_tweets(self, prompt):
        try:
            result = {}
            query, prompt_analysis = await self.generate_and_analyze_query(prompt)
            response = self.get_recent_tweets(prompt_analysis.api_params)

            if response.status_code in [429, 502, 503, 504]:
                bt.logging.warning(f"analyse_prompt_and_fetch_tweets status_code: {response.status_code} ===========, {response.text}")
                await asyncio.sleep(random.randint(15, 30))  # Wait for a random time between 15 to 25 seconds before retrying
                response = self.get_recent_tweets(prompt_analysis.api_params)  # Retry fetching tweets
            
            if response.status_code == 400:
                bt.logging.warning(f"analyse_prompt_and_fetch_tweets: Try to fix bad tweets Query ============, {response.text}")
                response, prompt_analysis = await self.retry_with_fixed_query(prompt=prompt, old_query=prompt_analysis, error=response.text)

            if response.status_code != 200:
                bt.logging.error(f"Tweets Query ===================================================, {response.text}")
                raise Exception(F"analyse_prompt_and_fetch_tweets: {response.text}")
            
            result_json = response.json()
            tweets_amount = result_json.get('meta', {}).get('result_count', 0)
            if tweets_amount == 0:
                bt.logging.info("analyse_prompt_and_fetch_tweets: No tweets found, attempting next query.")
                response, prompt_analysis = await self.retry_with_fixed_query(prompt, old_query=prompt_analysis, is_accuracy=False)
                result_json = response.json() 
            
            bt.logging.trace("Tweets fetched ===================================================")
            bt.logging.trace(result)
            bt.logging.trace("================================================================")

            bt.logging.info(f"Tweets fetched amount ============= {tweets_amount}")

            return result_json, prompt_analysis
        except Exception as e:
            bt.logging.error(f"analyse_prompt_and_fetch_tweets, {e}")
            raise e
        
    async def generate_and_analyze_query(self, prompt):
        query = await self.generate_query_params_from_prompt(prompt)
        prompt_analysis = TwitterPromptAnalysisResult()
        prompt_analysis.fill(query)
        self.set_max_results(prompt_analysis.api_params)
        bt.logging.info("Tweets Query ===================================================")
        bt.logging.info(prompt_analysis)
        bt.logging.info("================================================================")
        return query, prompt_analysis

    def set_max_results(self, api_params, max_results=10):
        api_params['max_results'] = max_results

    async def retry_with_fixed_query(self, prompt, old_query, error= None, is_accuracy=True):
        new_query = await self.fix_twitter_query(prompt=prompt, query=old_query, error=error, is_accuracy=is_accuracy)
        prompt_analysis = TwitterPromptAnalysisResult()
        prompt_analysis.fill(new_query)
        self.set_max_results(prompt_analysis.api_params)
        result = self.get_recent_tweets(prompt_analysis.api_params)
        return result, prompt_analysis

    @staticmethod
    def extract_tweet_id(url: str) -> str:
        """
        Extract the tweet ID from a Twitter URL.

        Args:
            url: The Twitter URL to extract the tweet ID from.

        Returns:
            The extracted tweet ID.
        """
        match = re.search(r'/status(?:es)?/(\d+)', url)
        return match.group(1) if match else None

    def fetch_twitter_data_for_links(self, links: List[str]) -> List[dict]:
        tweet_ids = [self.extract_tweet_id(link) for link in links if self.is_valid_twitter_link(link)]
        return self.get_tweets_by_ids(tweet_ids)
    
    def is_valid_twitter_link(self, url: str) -> bool:
        """
        Check if the given URL is a valid Twitter link.

        Args:
            url: The URL to check.

        Returns:
            True if the URL is a valid Twitter link, False otherwise.
        """
        parsed_url = urlparse(url)
        return parsed_url.netloc.lower() in VALID_DOMAINS
    

    def find_twitter_links(self, text: str) -> List[str]:
        """
        Find all Twitter links in the given text.

        Args:
            text: The text to search for Twitter links.

        Returns:
            A list of found Twitter links.
        """
        return self.twitter_link_regex.findall(text)

if __name__ == "__main__":
    client = TwitterAPIClient()
    # result = asyncio.run(client.analyse_prompt_and_fetch_tweets("Get tweets from user @gigch_eth"))

    dt = MockTwitterQuestionsDataset()
    questions = []
    for topic in dt.topics:
        questions = []
        for template in dt.question_templates:
            question = template.format(topic)
            questions.append(question)

        results = asyncio.run(asyncio.gather(*(client.analyse_prompt_and_fetch_tweets(question) for question in questions)))
        for (result_json, prompt_analysis), qs in zip(results, questions):
            tweets_amount = result_json.get('meta', {}).get('result_count', 0)
            if tweets_amount <= 0:
                print("=====================START result_json=======================================")
                print(tweets_amount, "     ===  ", question)
                print("   ")
                print("=====================START prompt_analysis =======================================")
                print(prompt_analysis.api_params)
                print("=====================END prompt_analysis =======================================")
                print("=====================END result_json=======================================")