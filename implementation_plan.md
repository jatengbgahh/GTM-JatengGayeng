# GTM JatengGayeng Bot Implementation

We will implement the bot using Python and the `python-telegram-bot` library, which is the most robust and standard library for building Telegram bots in Python. We will use its `ConversationHandler` to manage the multi-step user flow.

## User Review Required

> [!WARNING]
> Please review the mocked data approach in the open questions below. Since we don't have the actual data sources or database yet, the bot will use dummy data and log the output to the console.

## Open Questions

> [!IMPORTANT]
> 1. **Data Sources**: For now, I will use mock data for "Branch" (e.g., Branch A, Branch B) and "WOK" (e.g., WOK 1, WOK 2). Is that acceptable for the initial version?
> 2. **Storage**: Upon clicking "Submit", I will simply print the gathered data to the terminal/logger. We can add actual database logic once the backend is known. Is this okay?
> 3. **Bot Token**: You will need to provide a Telegram Bot Token (from BotFather). You can either put it in a `.env` file or provide it when running the bot.

## Proposed Changes

We will create the following Python project structure in `d:\Kerjaan\Project\GTM-JatengGayeng`:

### Project Setup
#### [NEW] [requirements.txt](file:///d:/Kerjaan/Project/GTM-JatengGayeng/requirements.txt)
Will contain the required dependencies:
- `python-telegram-bot`
- `python-dotenv` (for loading environment variables)

#### [NEW] [.env.example](file:///d:/Kerjaan/Project/GTM-JatengGayeng/.env.example)
Template for the environment variables:
```
TELEGRAM_BOT_TOKEN=your_token_here
```

### Application Code
#### [NEW] [config.py](file:///d:/Kerjaan/Project/GTM-JatengGayeng/config.py)
Handles loading environment variables from `.env`.

#### [NEW] [mock_data.py](file:///d:/Kerjaan/Project/GTM-JatengGayeng/mock_data.py)
Contains hardcoded mock data for Branches and WOKs.

#### [NEW] [handlers.py](file:///d:/Kerjaan/Project/GTM-JatengGayeng/handlers.py)
Contains the `ConversationHandler` definition and all state functions:
- `start`: Shows Branch inline keyboard
- `select_branch`: Stores branch, shows WOK inline keyboard
- `select_wok`: Stores WOK, asks for Event Name
- `input_event_name`: Stores name, asks for Location Tag
- `input_location`: Stores location, shows summary and Submit button
- `submit_data`: Logs the final data and ends conversation
- `cancel`: Fallback to exit the flow

#### [NEW] [bot.py](file:///d:/Kerjaan/Project/GTM-JatengGayeng/bot.py)
Main entry point to initialize the bot and start polling.

## Verification Plan

### Manual Verification
1. I will set up the Python project structure and write the code.
2. I will ask you to create a `.env` file with your Telegram Bot Token.
3. You will run the bot locally and test the `/start` flow through your Telegram app to ensure it handles all states and edge cases correctly.
