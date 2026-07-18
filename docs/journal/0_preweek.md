# Technical Journal


## Technical Goal
The technical goal of the preweek is to determine how well the different agent architectures fit our business use-case.

My personal goal in addition to this is to gain a better understanding of 'skills' and how they actually differ from using the agent without a defined skill. In addition, I was really interested to see the difference between Claude Code and Kiro CLI in implementing the same task.

## Technical Uncertainty
- Uncertain whether a coding harness is able to interact with MUD without any interface or SDK
- Uncertain whether coding harness's agentic loop is effective enough to drive this type of workload that is not coding-related. The tasks and actions are less defined that in coding and the agent needs to be able to be in some ways more creative and use its own initiative to complete a goal.
- Uncertain whether LLM model's reasoning is sufficient to hold memory and drive decisions for this use case.
- Uncertain whether there will be enough visibility to determine whether the agent is working in an effective way.
- Uncertain whether the workflow with Kiro CLI will differ from the instructor's workflow with Claude Code.

## Technical Hypotheses 
There could be issues with the coding harness driving the MUD without an interface as there is no defined API. Managing a long-lived telnet session without an interface can be challenging or make game progression impossible.

General agent's biggest challenge will be managing memory as it would need to gain experience of the MUD world and its progress so far. If the memory is not managed in a reliable way, the agent is not able to continue a consistent loop throughout the game.

There are several reasons, such as need for observability (knowing what agent does and why it has taken certain decisions) and memory, as explained above, would make an implementating our own agent with SDK necessary.

## Technical Observations
Using Kiro CLI provided a very similar experience to using Claude Code and the different coding harnesses didn't seem to have major differences. Both seemed to straight away consider only one solution for the implementation: creating a skill file and a Python script for managing the connection to the game. A small difference that I observed, was Kiro CLI at times providing more visibility to the steps it was taking and it's decision-making process than Claude Code seemed to do in the instructor's video. 

Managing the agents permissions seemed cumbersome in both harnesses. They were asking for approval for every step of the Python script creation, which makes the process slow and labour-intensive. An alternative would be to give it approval to create any Python scripts, which would have considerable risks as Python scripts can do a lot of things on your local machine. There should be a way to have a more specialised agent that will not implement something that is out of scope.

I found the difference between Claude Haiku 4.5 and Claude Sonnet 4.6 models' behaviour quite interesting - Haiku was clearly more concentrated on the exact instructions we had given to it and lacked the capacity to use its own initiative. For example, it was more more willing to modify its own tools, change its strategy and investigate missing steps. Full explanations of different scenarios and models' behaviour examples can be found in [the explore architecture documentation](/docs/explore_architectures.md).


## Technical Conclusions

Using an agent skill would be a suitable solution if you wanted to complete only a certain action in a game - if you had some kind of short-term goal that you wanted to achieve. That would work quite well, especially after you have the working Python script that will manage the connection and if you are using a model like Claude Sonnet 4.6 that can reason better than Haiku. However, managing a long-term connection and an ongoing game has several differences. 

It does seem that if you want the agent to be able to play the game progressively, learn about the world as it discovers more and keep track of its progress, a custom agent is required and its creation is justified. 



## Key Takeaway
Whether using a plain agent or a skill, the main challenge seems to be the same that I have observed until now in other projects: there is not enough visibility to the agent's behaviour or decision-making and there is no easy solution for managing memory.