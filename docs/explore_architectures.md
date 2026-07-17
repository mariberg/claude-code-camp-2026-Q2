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