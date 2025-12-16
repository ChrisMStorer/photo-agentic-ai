# my awesome assistant
This project implements an AI agent that saves notes.  The agent will save a note for you to the local file system.

This is a work-in-progress.  

This project can be deployed to Vercel.


Bugs:
- Notes cannot be saved in Vercel's file system, so the save functionality doesn't work in Vercel.
- The agent is not very proactive - keeps prompting for details.
- The agent is not aware of context from the previous command.
  
To use locally:
- "pip install" everything in the requirements.txt file
- Uncomment the "uvicorn" lines in main.py.
- run "python main.py".

To deploy and run in Vercel:
- You must have an account set up in Vercel
- Comment the "uvicorn" lines in main.py.
- Install the Vercel CLI tool
  - npm i -g vercel
  - Invoke "vercel", then sign in using the browser if necessary.
- Deploy using vercel
  - vc deploy
  - Open the "Inspect" link to go into the Vercel deployment.