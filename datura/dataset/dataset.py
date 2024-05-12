import random
import datetime
import bittensor as bt
from datasets import load_dataset
from bs4 import BeautifulSoup
import time
import requests


class MockTwitterQuestionsDataset:
    def __init__(self):
        # Extended list of templates for questions

        self.question_templates = [
            "What are the latest {} insights?",
            "Can you provide the most up-to-date information on the {}?",
            "What's the current chatter on Twitter regarding {}?",
            "Any newsworthy tweets about {} recently?",
            "What are the latest trending tweets about {}?",
            "What's currently making waves on Twitter about {}?",
            "What's the freshest discussion on Twitter concerning {}?",
            "Any latest developments in {} on Twitter?",
            "What are the most recent Twitter polls about {}?",
            "How is Twitter reacting to {}?",
            "What are the latest tweets concerning {}?",
            "What are the dominant opinions on Twitter regarding {}?",
            "How is the Twitterverse engaging with {}?",
            "What's being debated on Twitter concerning {}?",
            "Which Twitter hashtags are now associated with {}?",
            "What's the current sentiment about the {}?",
            "How are {} revolutionizing trends in 2024?",
            "What's novel in the domain of {}?",
            "Recent progress in {}",
            "What are the latest trends in {}?",
            "Newest insights in {}",
            "Latest updates on {} initiatives",
            "New findings in {}",
            "What's unfolding in {}?",
            "The newest in {} news",
            "Latest developments in {}",
            "Recent breakthroughs in {}",
            "Newest in {} technology",
            "Current leading practices for {}",
            "The most recent updates in {}",
            "Innovative techniques in {}",
            "The current dynamics of {}",
            "New perspectives in {}",
            "The latest findings on {}",
            "New breakthroughs in {}",
            "Current discussions in {}",
            "The latest on {} regulatory changes?",
            "The effect of {} on global markets?",
            "The newest breakthroughs in {}?",
            "Trends shaping the {} this year?",
            "Innovations in {} shaping the sector?",
            "Major challenges in the {} today?",
            "The evolution of {} through innovation?",
            "Key factors driving {} innovation?",
            "The effect of {} regulations on the industry?",
            "The role of {} in the modern economy?",
            "{}'s impact on consumer trends?",
            "Latest movements in {} startups?",
            "What's new in the {} landscape?",
            "{}'s contribution to sustainability?",
            "Forecasts for {} in the near future?",
            "{}'s strategy for climate action?",
            "Emerging tech in {}?",
            "Investment patterns in {}?",
            "Future outlook for {}?",
            "Edge advancements in {} technology?",
            "{}'s societal impact in 2024?",
            "Emerging startups in the {} sector?",
            "Ethical debates around {}?",
            "Policy adaptations to {} challenges?",
            "The economic significance of {} in 2024?",
            "{}'s role in altering the global scene?",
            "Long-term effects of {} on society?",
            "Current debates surrounding {}?",
            "Forecasts for {}'s future?",
            "Innovative approaches in {} today?",
            "{}'s everyday influence in 2024?",
            "Latest collaborations in the {} industry?",
            "{}'s impact on culture in 2024?",
            "Recent government policies on {}?",
            "The latest updates in {} initiatives",
            "New research in {}",
            "The ongoing conversation in {}?",
            "The newest in {} news",
            "Latest stories about {}",
            "Recent triumphs in {}",
            "What's innovative in {} technology?",
            "Current exemplary practices in {}",
            "The latest intelligence in {}",
            "Innovations in {} practices",
            "The forefront of {}",
            "Insights on {}",
            "The latest analyses on {}",
            "Technologies transforming {}",
            "Active discussions in {}",
            "Regulatory changes impacting {}?",
            "The influence of {} on international markets?",
            "Latest innovations in {}?",
            "Defining trends in {} this year?",
            "How {} is transforming the industry?",
            "Current obstacles in {}?",
            "{}'s evolution through innovation?",
            "Drivers of {} progress?",
            "Impacts of {} regulations?",
            "{}'s position in the economic framework?",
            "Trends propelled by {}?",
            "Startups disrupting {}?",
            "The {} ecosystem today?",
            "Efforts towards sustainability in {}?",
            "Projections for {}?",
            "Strategies against climate change in {}?",
            "Pioneering technologies in {}?",
        ]

        #     "What are the latest {} developments?",
        #     "Can you provide the most recent updates on the {}?",
        #     "What's the current buzz on Twitter regarding {}?",
        #     "Any fresh news tweets about {}?",
        #     "What are the latest viral tweets about {}?",
        #     "What's currently trending on Twitter about {}?",
        #     "What's the newest discussion on Twitter concerning {}?",
        #     "Any recent developments in {} on Twitter?",
        #     "What are the latest Twitter surveys about {}?",
        #     "How is Twitter responding to {}?",
        #     "What are the newest tweets about {}?",
        #     "What are the prevailing opinions on Twitter regarding {}?",
        #     "How is the Twitter community engaging with {}?",
        #     # "What humorous content about {} is being shared on Twitter?",
        #     "What's being talked about on Twitter concerning {}?",
        #     "Which Twitter hashtags are currently linked with {}?",
        #     "What's the latest sentiment about the {}?",
        #     "How are {} innovating recipes in 2024?",
        #     "What's new in the realm of {}?",
        #     "Recent advancements in {}",
        #     "What are the current trends in {}?",
        #     "Latest discoveries in {}",
        #     "Updates on {} projects",
        #     "Newest findings in {}",
        #     "What's happening in {}?",
        #     "The latest in {} news",
        #     "New developments in {}",
        #     "Recent milestones in {}",
        #     "Latest in {} technology",
        #     "Current best practices for {}",
        #     "The latest updates in {}",
        #     "Innovative methods in {}",
        #     "The current state of {}",
        #     "Fresh perspectives in {}",
        #     "The latest on {}",
        #     "New innovations in {}",
        #     "Current themes in {}",
        #     "The latest on {} policy changes?",
        #     "The impact of {} on global markets?",
        #     "The latest breakthroughs in {}?",
        #     "Trends influencing the {} this year?",
        #     "Advancements in {} shaping the sector?",
        #     "Key challenges in the {} today?",
        #     "The evolution of {} via technology?",
        #     "Principal drivers of {} innovation?",
        #     "The impact of {} regulations on the sector?",
        #     "The role of {} in today's economy?",
        #     "{}'s influence on consumer behavior?",
        #     "New developments in {} startups?",
        #     "What's the latest in the {} scene?",
        #     "{}'s role in promoting sustainability?",
        #     "Predictions for {} in the upcoming years?",
        #     "{}'s approach to combating climate change?",
        #     "Emerging technologies within {}?",
        #     # "The global impact of {}?",
        #     "Investment trends in {}?",
        #     "Future prospects for {}?",
        #     "Cutting-edge advancements in {} technology?",
        #     "{}'s influence on society in 2024?",
        #     "Rising startups in the {} industry?",
        #     "Ethical considerations around {}?",
        #     "Policy responses to {} challenges?",
        #     "The economic impact of {} in 2024?",
        #     "{}'s role in reshaping the global landscape?",
        #     "Long-term impacts of {} on society?",
        #     "Ongoing controversies surrounding {}?",
        #     "Predictions for {}?",
        #     "Innovative strategies within {} today?",
        #     "{}'s daily impact in 2024?",
        #     "Recent partnerships in the {} industry?",
        #     "{}'s influence on pop culture in 2024?",
        #     "Latest government regulations regarding {}?",
        #     "The newest updates on {} projects",
        #     "Recent findings in {}",
        #     "The current talk in {}?",
        #     "The latest news in {}",
        #     "Breaking news about {}",
        #     "Recent achievements in {}",
        #     "What's new in {} technology?",
        #     "Current best practices in {}",
        #     "The latest data in {}",
        #     "Innovations in {} methods",
        #     "The vanguard of {}",
        #     "Insights into {}",
        #     "The latest reports on {}",
        #     "Technologies defining {}",
        #     "Ongoing discussions in {}",
        #     "Policy changes affecting {}?",
        #     "The influence of {} on global markets?",
        #     "New breakthroughs in {}?",
        #     "Defining movements in {} this year?",
        #     "How {} is revolutionizing the sector?",
        #     "Present challenges in {}?",
        #     "{}'s development with technology?",
        #     "Catalysts of {} innovation?",
        #     "Consequences of {} regulations?",
        #     "{}'s status in the economic landscape?",
        #     "Trends driven by {}?",
        #     "Startups revolutionizing {}?",
        #     "The current {} landscape?",
        #     "Sustainability efforts in {}?",
        #     "Forecasts for {}?",
        #     "Climate change strategies in {}?",
        #     "Frontier technologies in {}?",
        # ]

        # self.question_templates = [
        #     "What are the latest {} happenings?",
        #     "Can you provide the latest updates on the {}?",
        #     "What's the current chatter on Twitter about {}?",
        #     "Any recent news tweets about {}?",
        #     "What are the latest viral tweets concerning {}?",
        #     "What's trending on Twitter now about {}?",
        #     "What's the latest discussion on Twitter about {}?",
        #     "Any new developments in {} on Twitter?",
        #     "What are the most recent Twitter polls about {}?",
        #     "How is Twitter reacting to {}?",
        #     "What are the latest tweets concerning {}?",
        #     "What are the dominant opinions on Twitter about {}?",
        #     "How is the Twitter community interacting with {}?",
        #     # "What humorous content about {} is being shared on Twitter?",
        #     "What's being discussed on Twitter regarding {}?",
        #     "Which Twitter hashtags are now associated with {}?",
        #     "What's the current sentiment about the {}?",
        #     "How are {} revolutionizing recipes in 2024?",
        #     "What's the latest in the world of {}?",
        #     "Recent progress in {}",
        #     "What are the latest trends in {}?",
        #     "Newest discoveries in {}",
        #     "Updates on {} initiatives",
        #     "Latest findings in {}",
        #     "What's going on in {}?",
        #     "The newest in {} news",
        #     "Latest developments in {}",
        #     "New milestones in {}",
        #     "Recent on {} technology",
        #     "Current best practices in {}",
        #     "The newest updates in {}",
        #     "Innovative techniques in {}",
        #     "The latest state of {}",
        #     "New perspectives in {}",
        #     "The newest on {}",
        #     "Recent innovations in {}",
        #     "Current topics in {}",
        #     "The latest about {} policy changes?",
        #     "The impact of {} on international markets?",
        #     "The newest breakthroughs in {}?",
        #     "Trends shaping the {} this year?",
        #     "Progress in {} shaping the sector?",
        #     "Major challenges in the {} today?",
        #     "The evolution of {} through technology?",
        #     "Key drivers of {} innovation?",
        #     "The impact of {} regulations on the industry?",
        #     "The role of {} in the modern economy?",
        #     "{}'s effect on consumer behavior?",
        #     "Latest developments in {} startups?",
        #     "What's new in the {} scene?",
        #     "{}'s contribution to sustainability?",
        #     "Forecasts for {} in the coming years?",
        #     "{}'s strategy against climate change?",
        #     "Emerging technologies in {}?",
        #     # "The global influence of {}?",
        #     "Trends in {} investments?",
        #     "Future outlook for {}?",
        #     "Leading-edge advancements in {} technology?",
        #     "{}'s impact on society in 2024?",
        #     "Emerging startups in the {} field?",
        #     "Ethical discussions around {}?",
        #     "Policy solutions to {} challenges?",
        #     "The economic significance of {} in 2024?",
        #     "{}'s role in transforming the global landscape?",
        #     "Long-term effects of {} on society?",
        #     "Current controversies around {}?",
        #     "Forecasts for {}?",
        #     "Innovative approaches within {} today?",
        #     "{}'s everyday impact in 2024?",
        #     "Latest partnerships in the {} sector?",
        #     "{}'s impact on pop culture in 2024?",
        #     "New government policies regarding {}?",
        #     "The latest on {} projects",
        #     "New findings in {}",
        #     "The current buzz in {}?",
        #     "The latest in {} news",
        #     "Breaking stories on {}",
        #     "Recent successes in {}",
        #     "What's new in {} tech?",
        #     "Best practices in {} currently",
        #     "The latest information in {}",
        #     "Innovations in {} techniques",
        #     "The forefront of {}",
        #     "Insights on {}",
        #     "Latest news on {}",
        #     "Technologies shaping {}",
        #     "Current discussions in {}",
        #     "Policy adjustments impacting {}?",
        #     "The effect of {} on global markets?",
        #     "New breakthroughs in {}?",
        #     "Defining trends in {} this year?",
        #     "How {} is transforming the sector?",
        #     "Current challenges in {}?",
        #     "{}'s evolution with technology?",
        #     "Drivers of {} innovation?",
        #     "Effects of {} regulations?",
        #     "{}'s position in the economic framework?",
        #     "Trends influenced by {}?",
        #     "Startups disrupting {}?",
        #     "Today's {} landscape?",
        #     "Efforts towards sustainability in {}?",
        #     "Projections for {}?",
        #     "Strategies against climate change in {}?",
        #     "Frontier technology in {}?",
        # ]

        # self.question_templates = [
        # "What are the recent {} events?",
        # "Tell me the recent news about the {}",
        # "What's the current sentiment on Twitter about {}?",
        # "Are there any breaking news tweets about {}?",
        # "What are the latest viral tweets about {}?",
        # "What's trending on Twitter about {}?",
        # "What's the latest discussion on Twitter about {}?",
        # "Are there any new developments in {} on Twitter?",
        # "What are the recent Twitter polls about {}?",
        # "How are Twitter users reacting to {}?",
        # "What are the recent tweets regarding {}?",
        # "What are the top opinions on Twitter about {}?",
        # "How is the Twitter community responding to {}?",
        # # "What humorous content about {} is being shared on Twitter?",
        # "What are Twitter users saying about {}?",
        # "What Twitter hashtags are currently associated with {}?",
        # "What is the current sentiment about the {}?",
        # "How are {} spicing up the recipes in 2024?",
        # "What are the recent developments in {}?",
        # "Latest advancements in {}",
        # "Current trends in {}",
        # "Recent discoveries in {}",
        # "Updates on {} efforts",
        # "New findings in {}",
        # "Current events in {}",
        # "Latest {} news",
        # "Breaking news in {}",
        # "Recent achievements in {}",
        # "Updates on {} technology",
        # "Current best practices in {}",
        # "Latest news in {}",
        # "New methods in {}",
        # "Current state of {}",
        # "Latest findings in {}",
        # "Updates on {}",
        # "Recent innovations in {}",
        # "Current trends in {}",
        # "What's the latest in {} policy changes?",
        # "How is the {} impacting global markets?",
        # "What are the newest breakthroughs in {}?",
        # "What trends are defining the {} this year?",
        # "How are advancements in {} shaping the industry?",
        # "What are the main challenges facing the {} today?",
        # "How is the {} evolving with technology?",
        # "What are the key factors driving {} innovation?",
        # "How are {} regulations affecting the market?",
        # "What role does {} play in the modern economy?",
        # "How is {} influencing consumer behavior?",
        # "What are the recent developments in {} startups?",
        # "What's new in the world of {}?",
        # "How is {} contributing to sustainability?",
        # "What are the latest predictions for {} in the coming years?",
        # "How is the {} addressing climate change?",
        # "What are the emerging technologies in {}?",
        # # "How is {} affecting international relations?",
        # "What are the current trends in {} investment?",
        # "What's the future outlook for {}?",
        # "What are the latest advancements in {} technology?",
        # "How is {} impacting society in 2024?",
        # "What are the most promising startups in the {} industry?",
        # "What are the ethical considerations surrounding {}?",
        # "How are policymakers addressing challenges in {}?",
        # "What are the economic implications of {} in 2024?",
        # "How is {} transforming the global landscape?",
        # "What are the potential long-term effects of {} on humanity?",
        # "What are the latest controversies surrounding {}?",
        # "How are experts predicting the future of {}?",
        # "What are the most innovative solutions in {} today?",
        # "How is {} affecting people's daily lives in 2024?",
        # "What are the latest collaborations in the {} industry?",
        # "How is {} influencing pop culture in 2024?",
        # "What are the latest government initiatives related to {}?",
        # ]

        # Expanded list of topics, focusing on commonly discussed themes on Twitter

        self.topics = [
            "renewable energy",
            "stock market",
            "artificial intelligence",
            "fashion",
            "space exploration",
            "climate change",
            "nutrition",
            "diet",
            "international politics",
            "movies",
            "entertainment",
            "technology",
            "gadgets",
            "medical research",
            "electric vehicles",
            "software development",
            "education",
            "online learning",
            "sustainable agriculture",
            "economic recovery",
            "psychology",
            "mental health",
            "cybersecurity",
            "data privacy",
            "architecture",
            "design",
            "travel",
            "tourism",
            "USA",
            "tech",
            "startup",
            "entrepreneurship",
            "world issues",
            "global issues",
            "music",
            "live performances",
            "film",
            "cinema",
            "sport",
            "fitness",
            "gaming",
            "esports",
            "health",
            "wellness",
            "streaming services",
            "cryptocurrency",
            "blockchain",
            "climate sustainability",
            "machine learning",
            "American politics",
            "elections",
            "finance",
            "global politics",
            "diplomacy",
            "Olympics",
            "sports competitions",
            "social media",
            "digital communication",
            "art",
            "culture",
            "healthcare",
            "medical",
            "entrepreneurship",
            "Nvidia AI",
            "Ukraine",
            "geopolitics",
            "Google digital innovation",
            "programming",
            "software development",
            "science",
            "research",
            "history",
            "cultural",
            "cryptocurrency",
            "blockchain technology",
            "movies",
            "digital health",
            "travel",
            "coffee culture",
            "lifestyle",
            "economy",
            "financial markets",
            "internet culture",
            "social media trends",
            "indie games",
            "game design",
            "video game development",
            "technology",
            ".NET framework",
            "programming",
            "Bitcoin",
            "digital currency",
            "fitness",
            "health technology",
            "robotics technology",
            "automation",
            "cinema",
            "movie industry",
            "tech innovation",
            "gadgets",
            "venture capital",
            "geopolitics",
            "artists",
            "directors",
            "competitions",
            "health and wellness",
            "designers",
            "game development",
            "original series",
            "green technology",
            "data science",
            "adventure",
            "US news",
            "investing",
            "voting",
            "world events",
            "content creation",
            "exhibitions",
            "SpaceX",
            "international relations",
            "digital services",
            "cloud services",
            "open-source",
            "AI-generated imagery",
            "digital art",
            "cosmos",
            "clean energy",
            "new media art",
            "automotive technology",
            "sustainable practices",
            "unmanned aerial vehicles",
            "digital finance",
            "digital currency trading",
            "relaxation",
            "global economy",
            "viral content",
            "creative gaming",
            "Microsoft",
            "blockchain technology",
            "machine learning applications",
            "Internet of Things",
            "crypto community",
            "fiscal policy",
            "agricultural technology",
            "innovation",
            "virtual reality",
            "affordable housing",
            "mental health awareness",
            "public transportation",
            "e-commerce",
            "renewable energy transition",
            "autonomous vehicles",
            "data privacy",
            "international trade agreements",
            "urban development",
            "quantum computing",
            "global migration patterns",
            "venture capital",
            "space tourism",
            "google",
            "amazon",
            "microsoft",
            "twitter",
            "quantum mechanics",
            "cybersecurity",
            "augmented reality",
            "smart cities",
            "biotechnology",
            "autonomous driving",
            "5G networks",
            "gene editing",
            "smart homes",
            "blockchain governance",
            "digital identity",
            "sustainable fashion",
            "circular economy",
            "carbon capture technology",
            "precision agriculture",
            "telemedicine",
            "online education platforms",
            "remote work",
            "digital nomads",
            "plant-based meat alternatives",
            "vertical farming",
            "3D printing",
            "robotics in healthcare",
            "edge computing",
            "digital twins",
            "haptic technology",
            "brain-computer interfaces",
            "decentralized finance (DeFi)",
            "non-fungible tokens (NFTs)",
            "space mining",
            "asteroid detection",
            "quantum cryptography",
            "smart materials",
            "green hydrogen",
            "tidal energy",
            "carbon offsetting",
            "regenerative agriculture",
            "precision medicine",
            "personalized nutrition",
            "mental health apps",
            "virtual events",
            "augmented reality shopping",
            "drone delivery",
            "self-driving trucks",
            "hyperloop transportation",
            "digital art galleries",
            "virtual influencers",
            "social media activism",
            "gamification in education",
            "bioplastics",
            "ocean cleanup technology",
            "smart waste management",
            "carbon-negative construction",
            "home gardening",
            "local tourism",
            "DIY crafts",
            "home workouts",
            "budget travel",
            "street food",
            "local markets",
            "community service",
            "public parks",
            "urban cycling",
            "pet care",
            "indoor plants",
            "homemade recipes",
            "thrifting",
            "podcasts",
            "audiobooks",
            "e-books",
            "mobile apps",
            "video blogging",
            "online courses",
            "language learning",
            "coding for beginners",
            "yoga",
            "meditation",
            "mental wellness",
            "stress management",
            "time management",
            "personal finance",
            "saving tips",
            "investment basics",
            "easy cooking",
            "meal planning",
            "food preservation",
            "sustainable living",
            "eco-friendly habits",
            "recycling tips",
            "zero waste lifestyle",
            "minimalist living",
            "upcycling projects",
            "handicrafts",
            "digital photography",
            "smartphone videography",
            "social media marketing",
            "blogging tips",
            "freelancing",
            "remote work tools",
            "virtual meetings",
            "online security",
            "privacy protection",
            "cyber hygiene",
            "Ukraine",
            "Brazil",
            "India",
            "China",
            "Germany",
            "France",
            "Italy",
            "Japan",
            "Canada",
            "Australia",
            "South Korea",
            "Russia",
            "Spain",
            "Mexico",
            "Indonesia",
            "Turkey",
            "United Kingdom",
            "Saudi Arabia",
            "Netherlands",
            "Switzerland",
            "Sweden",
            "Belgium",
            "Poland",
            "Argentina",
            "Norway",
            "Iran",
            "Thailand",
            "South Africa",
            "Egypt",
            "Pakistan",
            "Bangladesh",
            "Vietnam",
            "Philippines",
            "Iraq",
            "Afghanistan",
            "Nigeria",
            "Ethiopia",
            "Morocco",
            "Ghana",
            "Kenya",
            "Uganda",
            "Zimbabwe",
            "Chile",
            "Colombia",
            "Peru",
            "Venezuela",
            "Cuba",
            "Malaysia",
            "Singapore",
            "Kazakhstan",
            "Uzbekistan",
            "Syria",
            "Jordan",
            "Lebanon",
            "Israel",
            "Denmark",
            "Finland",
            "Ireland",
            "cryptocurrency",
            "virtual reality",
            "climate change",
            "artificial intelligence",
            "blockchain",
            "sustainable energy",
            "electric vehicles",
            "space exploration",
            "cybersecurity",
            "digital health",
            "remote work",
            "e-commerce",
            "quantum computing",
            "5G technology",
            "augmented reality",
            "smart cities",
            "gene editing",
            "autonomous driving",
            "machine learning",
            "data privacy",
            "fintech",
            "gig economy",
            "internet of things",
            "nanotechnology",
            "renewable energy",
            "social media trends",
            "digital marketing",
            "biohacking",
            "agritech",
            "edtech",
            "wearable tech",
            "gaming",
            "deep learning",
            "cloud computing",
            "mental health",
            "personal finance",
            "zero waste lifestyle",
            "plant-based diets",
            "telemedicine",
            "content creation",
        ]

    def generate_question(self):
        # Randomly select a question template and a topic
        template = random.choice(self.question_templates)
        topic = random.choice(self.topics)

        # Generate a question
        return template.format(topic)

    def next(self):
        # Return a generated question
        return self.generate_question()


class MockDiscordQuestionsDataset:
    def __init__(self):
        self.question_templates = [
            "What are the recent announcements in #alpha",  # in:alpha announcements
            "What are the recent announcements in #announcements",  # in:announcements
            "Tell me the recent news about bittensor",  # bittensor news
            "What @professor is asking in subnet 22",  # from:professor in:22
            "What is latest release version of Bittensor?",  # bittensor release
            "What are the Hyper parameters of subnet 22?",  # hyper parameters in:22
            "What people are talking about TAO wallet?",  # TAO wallet
            "Axon configurations in translation subnet",  # axon config in:translation
            "What are the recent discussions about the new bittensor server update?",  # bittensor server update
            "How do I configure my axon for the image classification subnet?",  # axon image classification
            "What are people saying about the new Datura tokenomics proposal?",  # datura tokenomics
            "Has there been any news on the upcoming Bittensor hackathon?",  # bittensor hackathon
            "What are the system requirements for running a full datura node?",  # system requirements chi model
            "How can I stake my TAO tokens and earn rewards?",  # stake tao tokens
            "What are the latest performance benchmarks for different subnet configurations?",  # performance benchmarks days_before:3d
            "Are there any updates on the integration with other AI platforms?",  # bittensor integrations
            "What's the best way to contribute to the Bittensor codebase as a developer?",  # contribute bittensor codebase
            "What people discussed today?",  # days_before:1d
            "How can we deploy a subnet",  # subnet deployment or deploy subnet
            "Test network",  # test network
            "Which subnets has implementation of Youtube Search tool?",  # subnet youtube search
            "Which subnets can interact with Google",  # subnet google
            "Is there any subnet that generates images?",  # subnet image generation
            "When testnet will be fixed?",  # testnet issue
            "Whats the best image generation tool on bittensor?",  # image generation tool
        ]

    def generate_question(self):
        template = random.choice(self.question_templates)
        return template

    def next(self):
        return self.generate_question()


if __name__ == "__main__":
    # Example usage
    twitter_questions_dataset = MockTwitterQuestionsDataset()
    for _ in range(100):
        print(twitter_questions_dataset.next())
