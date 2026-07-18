# Explore Agent Architectures

The hardest decision is selecting between different agent solutions as their responsibilities often overlap. For this reason, multiple agent
architectures are explored in order to determine the best fit for our agent workload.


1. An Agent file with references files, e.g. AGENTS.md @~/docs/*.md

The most simple agent format is creating an 'agent' file and possibly other files that could be read conditionally when needed.
The coding harness would use the agent file (```AGENTS.md``` for Kiro) to get some context of the situation in terms of being a player in tbaMUD and the port where the game is running and it would try to determine its actions and next steps based on the information we give to it.

This exploration was started by using the smallest and least intelligent model in order to make sure that most cost-efficient solutions are used where possible.

## Technical Observations

I started with Haiku 4.5 and created ```AGENTS.md``` which provided general guidelines for Kiro. It provided information about where the MUD is running and which login details can be used to play the game. The file explained that the agent can manage its own local memory via simple markdown files (```/data.player.md``` and ```/data/world.md```). The simple prompt given to the LLM was 'Can you find the bakery and list out the menu'.

It tried to establish a connection by creating temporary files to manage an nc connection and execute commands. The agent kept iterating and improving the script, however, it didn't manage to connect to the game. Increasing the model intelligence to Sonnet 4.6 did not help. 

The agent did update some data in the markdown files, although the information there is slightly confusing as one of the files is saying it is trying to connect to localhost:4000 and the other claims it has already connected and is starting exploration for bakery, although at no point was the agent actually able to log in to the game.

I did not experience with Kiro what seemed to happen with Claude Code in the instruction video, where it was trying to read local files, not pertaining to the loop, which took it take off task and wasted tokens/usage. Kiro remained during this exercise strictly in trying to rewrite the script that would help it establish a connection to the game.


## Technical Conclusions

There are other solutions that could make it easier for the model to login to the game, such as writing a better prompt or creating an artifact that would give full knowledge of the MUD's text interface, however, for such a fixed esperience a script would work better and prevent us from wasting tokens. 

It seems justified to build our own MUD SDK to connect to the MUD since the agent wants to manage the connection via script and execute common commands over the port. An MCP server to our MUD SDK could potentially drive the agent better at this architectural level. 

Managing the state by updating markdown files is also probably not sufficient as the world and player state are quite complex. 

Based on this, we can conclude that coding harnesses are best used for coding and for specialised agents it can be more productive to make your own loop.


## 2. Agent Skills driven by the main agent e.g. ~skills

An Agent Skill is a common way to drive specific functionality. It is an open format for agents adopted by many coding harnesses and agent SDKs.

I started by prompting Kiro (using Claude Sonnet) to create a skill for this task. It gave me a clear plan of the steps it was trying to implement:

```
Yes — I can create an Agent Skill. What I was doing before (probing the MUD's telnet handshake with Python) was research to inform the skill's connection script, not a detour from the task. That's a normal part of building it: I need to know the protocol details (raw telnet, ANSI codes, login prompts) before I can write a script that reliably logs in and issues commands.

Let me clarify what I found so far and confirm the plan before continuing:
  
What I confirmed:
  
- Server at localhost:4000 is a TBAMUD/DikuMUD-style MUD, plain telnet (with some IAC negotiation for ECHO/TERMTYPE).
- Login flow: prompt By what name do you wish to be known? → send dummy → prompt Password: → send helloworld → welcome banner → *** PRESS RETURN: prompt before reaching the game.
- Output is ANSI-colored text.

What a "skill" means here: an Agent Skill is a folder (in this case 02_agent_skills/) containing:
  
- SKILL.md — instructions/metadata (name, description, when to use it) that tells me how to use the skill
- Supporting scripts (e.g., a Python telnet client) that the skill's instructions reference, so I can connect, log in, send commands, and read responses on your behalf
  
My plan:
  
1. Write a Python script (mud_client.py) that handles connect/login/send-command/read-output as a small CLI tool.
2. Write SKILL.md describing the skill, credentials, and how to invoke the script.
3. Test it end-to-end against localhost:4000.
```

The harness then proceeded to write the script and markdown file. It managed to write a script that can handle the login but it straight away found
an edge case and it wanted to modify the script to take this info consideration:  a dangling connection that causes the next login to skip menu steps.

After the agent had created the python script and the skill, I prompted it to find the bakery and list the menu using the skill, which is was able to complete successfully:

<img width="1196" height="553" alt="image" src="https://github.com/user-attachments/assets/90a603f7-a194-4b0d-82c9-459667c2203d" />


The second prompt we gave it was to 'find the player's starting guild and practice kick'. Using Claude Haiku at this point, it was able to execute the task:

<img width="1140" height="113" alt="image" src="https://github.com/user-attachments/assets/712bac1b-be34-41ee-b617-25ade4297912" />


After that, using Sonnet we asked the agent to create a 'data' folder that would have md files that can retain persistent memory for the player. After this was implemented, the next ask given to Claude Haiku was: 'There is a massive minotaur in the newbie zone north of Midgaard. We want to defeat it, can you make this our primary goal and execute it'. Haiku started executing this goal and it was partially successful navigating to the correct location. It didn't find the massive minotaur but it found the newbie zone and started combat with creepy crawlers. However at this point it became confused with the logic of the game and quit the game before the combat was finished and for this reason it didn't gain any experience for the player. 

I then gave the agent more information where to find the massive minotaur and told it that it is in a 'red room' within the newbie zone. The agent searched through the newbie zone looking for the red room, however it then ran out of movement points and was not able to continue. After several attemps Claude Haiku was not able to figure out how to recover movement points - this means that it was not able to understand the basic functionality - even after giving it step-by-step instructions to sleep and wait for two minutes before waking up, it couldn't get that to work. Switching back to Claude Sonnet 4.6 resolved the problem immediately and it was able to add a 'recover' function to the script which worked. Claude Sonnet was able to also execute the instructions until the end - it found the correct room where the minotaur is located and analysed whether combat with it is possible:

<img width="1166" height="272" alt="image" src="https://github.com/user-attachments/assets/0686f0f2-f855-4c0a-8709-b5e42eae2d8f" />



## Technical Observations

I was able to use Kiro to create a skill that would reliably connect to MUD and play it using Claude Haiku 4.5/Sonnet 4.6.

Haiku was able to complete simple goals such as practising kick at the guild - and it reported back that the kick has been practised at the guild. When giving a broader task of defeating the massive minotaur in the newbie zone, it struggled to find the correct location within the newbie zone. It then very quickly ran out of movemement points, which meant that it got stuck. It seemed very helpless and unable to think of any solutions - it asked me how I would like to proceed and whether I know how to collect more movement points. It seemed to lack initiative and was completing the tasks only in the way that was given to it. 

Sonnet seemed to have more of its own initiative and behaved more like a 'real player'. It managed to fix the script that will allow it to sleep and recover movement points, it then found the correct command to open doors and figured out it needs to level up before fighting the minotaur. 

The agent did update the markdown files that store the world and player state, however, this was not done in real time which made it hard to observe what is happening. These markdown files would also become hard to manage when the memory grows - there needs to be a more organised way of managing state. It might also be a good idea to have some kind of 'player personas' that would allow it to implement more dynamic task management. It would then know in which way we want to play - whether taking risks or trying to play safe, etc. Otherwise the LLM will keep checking each time before taking actions which become very labour-intensive and defeats the purpose of using an agent.

Kiro's agentic loop (especially when using Claude Sonnet, although more explorations of different models could be made) seems to be a good driver for these tasks. However, this introduces a dependency as any changes to this coding harness' agentic loop would mean that our agent's behaviour could change in a way that we are not able to predict.


## Technical Conclusions

Agent Skills work in taking actions within the game; however, managing a more complex state, world and player management is difficult and there is simply not enough visibility on what is going on. It is currently difficult to view what exactly the agent is doing and what it is storing in its state. Furthermore, we don't have visibility into token usage. For this reason a custom agentic loop seems appropriate for these tasks. This would allow us to make the agent work in ways that works in this scenario - taking independent actions and asking less for instructions about what it should do. 

It would be helpful to see the goal decomposition or planning for any goal that we give it, so that we could see the reasoning behind any actions it is taking.
