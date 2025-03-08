<div align="center">
    <img src="https://github.com/Hrishikesh332/Model-Evaluation/blob/main/src/twelvelabs.png">
    <h1>Video to Text Arena</h1>
    <p>
        <strong> Advanced video analysis platform that compares the capabilities of different AI models for video understanding and analysis. </strong>
    </p>
</div>

## Overview

Model Evalaution for the Video Understanding for - Video to Text task is an open-source web application that leverages multiple AI models to provide comprehensive video analysis. The platform enables users to analyze videos using state-of-the-art models including Twelve Labs' Pegasus, OpenAI's GPT-4o, and Google's Gemini

For support or to join the conversation, visit our [Discord](https://discord.com/invite/Sh6BRfakJa).

## Prerequisites

- Do checkout the requirements file and the Instruction to setup locally.
- Python 3.9+
- Flask
- API keys for - Twelve Labs (required for pegasus-1.2 model and core functionality), OpenAI (optional, for gpt-4o model), Google Generative AI (optional, for gemini-1.5-pro analysis)


## Core Architectural Working

![Core Architectural Working](https://github.com/Hrishikesh332/Model-Evaluation/blob/main/src/flow-model-eval.png)

## Project Structure

```
Model-Evalaution/
├── app.py                  
├── static/                 
│   ├── css/
│   │   └── style.css      
│   ├── js/
│   │   └── main.js         
├── templates/
│   └── index.html         
├── .env                  
├── .gitignore             
├── videos/              
├── requirements.txt        
└── README.md
```


## API Key Setup

Twelve Labs API

1. Create an account at Twelve Labs
2. Generate an API key from your dashboard
3. Add the key to your .env file or connect it through the application UI
4. Do create the index and upload the video at Twelve Labs Playground to try it out with your videos


## Installation

1. Clone the repository
```
git clone https://github.com/yourusername/video-analysis-ai.git
cd model-evaluation
```
2. Install dependencies
```
pip install -r requirements.txt
```

3. Configure environment variables -

```
TWELVELABS_API_KEY=your_twelvelabs_api_key
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
APP_URL=your_deployed_app_url
```

4. Run the application -

```
python app.py
```

5. Navigate to `http://localhost:5000` in your browse
    

## User Flow

1. Select a Video Index -

Use the dropdown menu to choose from public indexes or your own private indexes if you've connected an API key


2. Choose a Video - 

Select a video from the available options in the chosen index


3. Ask Questions -

Type your query in the input box or select from the suggested questions.

4. View Analysis -

The results from different models will appear in split panels
Compare the different perspectives and insights from each model.

## Queries

For any doubts or help you can reach out to me via hrishikesh3321@gmail.com or ask in the [Discord Channel](https://discord.com/invite/Sh6BRfakJa)
