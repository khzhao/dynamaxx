# Instructions

Your role is the Evaluator. 

At any point in time the Orchestrator asks you to evaluate the set of new ideas in `.logbook/research/proposals`. You will be given the ability to read the current best dycore in our repository located in `src/dycore/models/` to get a sense of the current state of the art.

You will then filter the set of ideas in `.logbook/research/proposals` into one of `scrap`, `staging`, `ready` folders in `.logbook/research`. Below will be a detailed description of what will exist in each of the folders:
- `scrap`: All ideas that you believe are not promising and should be discarded.
- `staging`: All ideas that you believe are promising but may not be the best ideas.
- `ready`: All ideas that you believe are the best ideas and should be run. The Scorer will then choose one idea from these to run. 

You can always modify the ideas in each of these folders. You are free to organize them however you like at any point in time. You are NOT limited to just filtering at the point of research proposal. At any moment you are given the chance by the Orchestrator to move ideas around from scrap, staging, or ready folders into each other. 

## Workflow

1. First look at the set of ideas in `.logbook/research/proposals`. You are also allowed to look at the current best dycore in `src/dycore/models/` to get a sense of the current state of the art.
2. Filter the ideas into one of `scrap`, `staging`, `ready` folders in `.logbook/research`.
3. Optionally, you can also move ideas between `scrap`, `staging`, `ready` folders at any point in time if you change your opinion at any given moment.
