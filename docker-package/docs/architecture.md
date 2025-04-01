# Paul AI Chatbot System Architecture

This document describes the system architecture of the Paul AI Chatbot.

## System Architecture Diagram

```mermaid
---
config:
  theme: neutral
---
flowchart TD
    title["Paul AI Chatbot System Architecture"]
    direction LR
    style title fill:#ffffff,stroke:#333,stroke-width:2px,font-size:24px,font-weight:bold


    subgraph Frontend["Frontend"]
        UI["Chainlit UI"]
    end
    subgraph Backend["Backend"]
        APP["app.py"]
        AGENT["AgentExecutor"]
        LLM["ChatOpenAI"]
    end
    subgraph Tools["Tools"]
        PPT["PowerPointTranslator"]
        SQL["SQLQueryTool"]
    end
    subgraph subGraph3["External Services"]
        OPENAI["OpenAI API"]
        DB[("SQLite Database")]
    end
    UI -- User Input --> APP
    APP -- Response --> UI
    APP -- Initialize --> AGENT
    AGENT -- Invoke --> LLM & PPT & SQL
    LLM -- API Request --> OPENAI
    OPENAI -- Response --> LLM
    SQL -- Query --> DB
    DB -- Results --> SQL
    PPT -- File Processing --> UI
    UI -- File Upload --> PPT
    PPT -- Translation Request --> LLM
    LLM -- Translation Result --> PPT
    PPT -- Generate File --> UI
    UI:::frontend
    APP:::backend
    AGENT:::backend
    LLM:::backend
    PPT:::tools
    SQL:::tools
    OPENAI:::external
    DB:::external
    classDef frontend fill:#FFE5E5,stroke:#FF6B6B,stroke-width:2px
    classDef backend fill:#E5F3FF,stroke:#4DABF7,stroke-width:2px
    classDef tools fill:#E5FFE5,stroke:#51CF66,stroke-width:2px
    classDef external fill:#FFF3E5,stroke:#FFA94D,stroke-width:2px
    style Backend fill:transparent,stroke:#FFD600
```

## Component Description

### Frontend Layer
- **Chainlit UI**: Provides user interface, handles file uploads and displays results

### Backend Layer
- **app.py**: Main application entry point
- **AgentExecutor**: Coordinates execution between different tools and LLM
- **ChatOpenAI**: Handles communication with OpenAI API

### Tools Layer
- **PowerPointTranslator**: Handles PowerPoint file translation
- **SQLQueryTool**: Handles database queries

### External Services
- **OpenAI API**: Provides language model services
- **SQLite Database**: Stores data

## System Flow
1. User input through UI
2. `app.py` initializes AgentExecutor
3. AgentExecutor invokes appropriate tools based on request
4. Tools execute specific tasks (translation or query)
5. Results are returned to user through UI 