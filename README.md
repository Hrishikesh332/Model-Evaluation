<div align="center">
    <img src="https://github.com/Hrishikesh332/Model-Evaluation/blob/main/backend/src/twelvelabs-logo.png">
    <h1>Video to Text Arena</h1>
    <p>
        <strong> Advanced video analysis platform that compares the capabilities of different AI models for video understanding and analysis. </strong>
    </p>
</div>

## Overview

Model Evalaution for the Video Understanding for - Video to Text task is an open-source web application that leverages multiple AI models to provide comprehensive video analysis. The platform enables users to analyze videos using state-of-the-art models including Twelve Labs' Pegasus, OpenAI's GPT-4o, Google's Gemini and AWS Nova.

For support or to join the conversation, visit our [Discord](https://discord.com/invite/Sh6BRfakJa).


## Available AI Models

| Model Name                         | Available ✅ |
|-----------------------------------|--------------|
| `pegasus-1.2`                     | ✅           |
| `gemini-2.0-flash`   | ✅           |
| `gemini-2.5-pro`                 | ✅           |
| `gpt-4o`                         | ✅           |
| `nova-lite-v1:0`                         | ✅           |


## Prerequisites

- Do checkout the requirements file and the Instruction to setup locally.
- Python 3.9+
- Flask
- API keys for - Twelve Labs (required for pegasus-1.2 model and core functionality), OpenAI (optional, for gpt-4o model), Google Generative AI (optional, for gemini-1.5-pro analysis)


## Core Architectural Working

![Core Architectural Working](https://github.com/Hrishikesh332/Model-Evaluation/blob/main/backend/src/flow-model-eval.png)

## Project Structure

```
├── .gitignore
├── README.md
├── backend
    ├── .env.local
    ├── .gitignore
    ├── README.md
    ├── app.py
    ├── cache/
    ├── cache_manager.py
    ├── config.py
    ├── models
    │   ├── __init__.py
    │   ├── gemini_model.py
    │   ├── nova_model.py
    │   └── openai_model.py
    ├── optimize.py
    ├── performance.py
    ├── requirements.txt
    ├── routes
    │   ├── __init__.py
    │   └── api_routes.py
    ├── services
    │   ├── __init__.py
    │   ├── twelvelabs_service.py
    │   └── video_service.py
    └── src/
├── package-lock.json
└── www.video2text.com
    ├── .gitignore
    ├── API_STATE_MANAGEMENT.md
    ├── app
        ├── api
        │   ├── analyze/
        │   ├── connect
        │   │   └── route.ts
        │   ├── disconnect
        │   │   └── route.ts
        │   ├── indexes/
        │   ├── models
        │   │   └── route.ts
        │   ├── status
        │   │   └── route.ts
        │   ├── thumbnails
        │   │   └── [indexId]
        │   │   │   └── [videoId]
        │   │   │       └── route.ts
        │   └── video
        │   │   └── select
        │   │       └── route.ts
        ├── globals.css
        ├── layout.tsx
        ├── page.tsx
        ├── test-api
        │   └── page.tsx
        └── test-video-player
        │   └── page.tsx
    ├── components.json
    ├── components
        ├── Model-Evaluation.code-workspace
        ├── model-evaluation-platform.tsx
        ├── theme-provider.tsx
        ├── ui/
        └── video-player.tsx
    ├── config.env.example
    ├── env.setup.md
    ├── hooks/
    ├── lib
        ├── api.ts
        ├── types.ts
        └── utils.ts
    ├── next.config.mjs
    ├── package-lock.json
    ├── package.json
    ├── pnpm-lock.yaml
    ├── postcss.config.mjs
    ├── public/
    ├── styles
        └── globals.css
    └── tsconfig.json
```


## API Key Setup

Twelve Labs API

1. Create an account at Twelve Labs
2. Generate an API key from your dashboard
3. Add the key to your .env file or connect it through the application UI
4. Do create the index and upload the video at Twelve Labs Playground to try it out with your videos

    

## User Flow

1. Select a Video Index -

Use the dropdown menu to choose from public indexes or your own private indexes if you've connected your TwelveLabs API key


2. Choose a Video - 

Select a video from the available options in the chosen index


3. Ask Questions -

Type your query in the input box or select from the suggested questions.

4. View Analysis -

The results from different models will appear in split panels
Compare the different perspectives and insights from each model.



---

## Installation

Clone the repository
```
git clone https://github.com/Hrishikesh332/Model-Evaluation.git
cd model-evaluation
```

## Backend

1. Install dependencies
```
cd backend
pip install -r requirements.txt
```

2. Configure environment variables -

```
TWELVELABS_API_KEY=your_twelvelabs_api_key
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
APP_URL=your_deployed_app_url
```

3. Run the application -

```
python app.py
```

4. Navigate to `http://localhost:5000` in your browse.


## Frotend

Go back to the root folder of the repository

1. Install dependencies
```
cd www.video2text.com
npm install --legacy-peer-deps
```

2. Do make a file to connect the frontend with the backend - .env.local

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:5000
```
To run it locally, or the url can be replaced to the deployed link.

3. Run the application -
```
npm run dev
```
4. Navigate to `http://localhost:3000` in your browse to see the application.

---

## How once can contribute

### **Backend Steps**

---

### **Step 1 — Create Model Class**

Create a new model class.
Include all processing utilities required for that model inside this class.
Place the class in the `models/` directory as a separate file.

```bash
models/
 └── your_model.py
```

---

### **Step 2 — Update Configuration**

Add your model's configuration to **`config.py`**, including:

* Inference API URL
* Base endpoint URL

---

### **Step 3 — Register Your Model**

Update **`models/__init__.py`** to import and register your newly created model class.

---

### **Step 4 — Integrate With Main Application**

In **`app.py`**, register your model by:

* Importing the class
* Adding it to the `model_dict`

---

### **Step 5 — Add API Route**

Update **`routes/api_routes.py`** to include your model in the routing logic
(Add it to the `model_dict` here as well)

✅ Backend setup is complete — only minimal frontend adjustments are required next.

---

### **Frontend Steps**

---

### **Step 1 — Update API Service Types**

Add your model to `ModelStatus` interface in -

```
lib/api.ts
```

---

### **Step 2 — Update Model Availability Functions**

Modify **`components/model-evaluation-platform.tsx`** to -

* Include your model in the model selector
* Add the model-availability logic function

---

### Final Result

Your new model will now appear in the UI arena, ready for use and experimentation.




## Queries

For any doubts or help you can reach out to me via hrishikesh3321@gmail.com or ask in the [Discord Channel](https://discord.com/invite/Sh6BRfakJa)
