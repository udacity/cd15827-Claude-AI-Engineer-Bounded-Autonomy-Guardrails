# What are Exercises?

Exercises are **self-assessed, hands-on practice activities** that allow learners to apply one or more skills taught in a lesson. They help learners build confidence, strengthen understanding, and prepare for real-world professional tasks.

## Why are Exercises Important?

Exercises provide structured, focused practice that strengthens the job-ready skills taught in the lesson. They help learners deepen their understanding through active application, build independent thinking skills, and prepare for the final project in the course.

### Exercise Design

Exercises are designed to give learners focused practice on a specific lesson skill and reflect how practitioners apply that skill in real-world contexts.
High-quality exercises:

- Are tightly aligned to a clearly defined target skill.
- Use scenarios or contexts that improve engagement while remaining universally accessible. See [Real-World Content Guidelines](https://udacity.atlassian.net/wiki/spaces/CntStds/pages/2717777924/Real-World+Content+Guidelines) and [Accessibility Standards](https://udacity.atlassian.net/wiki/spaces/CntStds/pages/3071606805/Accessibility+Standards) for more information.
- Require learners to work at the mid to high levels of [Bloom’s Taxonomy](https://bokcenter.harvard.edu/taxonomies-learning): applying, analyzing, evaluating, or creating.
- Include only the scaffolding necessary to keep the focus on the intended skill.

#### ✅ Do This

- **Focus on one clearly defined skill,** e.g, *”Analyze a dataset using descriptive statistics.”*
- **Use a simple, realistic scenario,** e.g, *”You’ve been asked to validate incoming data before it’s loaded into the pipeline.”*
- **Require mid-to-high cognitive challenge,** e.g, *”Evaluate which model performs best and justify your choice.”*

#### ❌ Don’t Do This

- **Use vague or overly broad skills,** e.g, *”Work with data.”*
- **Include distracting or inaccessible scenarios,** e.g, *”Pretend you’re organizing a unicorn festival…”*
- **Reduce the task to low-level recall,** e.g, *”Copy this code and run it as-is.”*
- **Include instructional design details,** e.g., separate sections labeled *”Objectives”* and “*Prerequisites.”*

### Exercise Instructions

Exercise instructions provide learners with all the necessary information to complete the task successfully, while still requiring them to think independently and solve problems.
Effective instructions:

- Clearly state the goal or outcome of the exercise.
- List all requirements needed to complete the task.
- Avoid detailed, step-by-step directions that remove opportunities for decision-making.
- Use clear, direct language that avoids ambiguity.
- Reference any starter code, files, or tools the learner will use.

#### ✅ Do This

- **State what the learner will produce**, e.g., *”Create a function that returns the top three keywords.”*
- **List clear requirements,** e.g., *”Your solution must run without errors and handle empty input.”*
- **Reference resources,** e.g., *”Use the starter file provided in the workspace.”*

#### ❌ Don’t Do This

- **Write step-by-step recipes**, e.g., *”First click this, then type this, then run this exact command…”*
- **Add hidden requirements not listed elsewhere, e.g., “Your solution should also have a CLI mode.”**
- **Use ambiguous phrasing**, e.g., *”Make sure your analysis looks good.”*
- **Create a scenario that is too complex**, e.g., a scenario that requires multiple paragraphs to explain.
- **Set a scenario that is juvenile, silly, or not appropriate for a global audience**, e.g., *”Pretend you’re organizing a unicorn festival for a group of magical forest creatures...”, “Create a database to track the inventory and vintage of a wine cellar”, “Build an algorithm for a dating app that matches users based on their relationship goals”*

### Starter and Solution Code for Coding Exercises

The starter and solution code must clearly communicate the task and demonstrate strong coding practices.

- Starter code uses TODO comments to indicate required work.
- Solution code replaces TODO comments with clear, descriptive comments.
- Example code follows the style, structure, and conventions learners are expected to use.

#### Example (Starter Code)

```python
class Agent:
    #TODO: Create a constructor with required parameters
    def __init__(self):
        #TODO: Instantiate the client
        self.agent = OpenAI()

    #TODO: Create the logic for an invoke() method
    def invoke(self, message: str) -> str:
        return
```

#### Example (Solution Code)

```python
class Agent:
    # Initiate the agent
    def __init__(self):
        # Instantiate the client
        self.agent = OpenAI()

    # Invoke the client
    def invoke(self, message: str) -> str:

        return
```

### Solutions

Solutions help learners verify their work, understand the correct approach, and learn from mistakes. In most cases, the solution page will include a video, text, and any relevant code or artifact examples.

#### Solution Video

A concise **video walkthrough** is provided for many exercises.

- The video follows the key steps outlined in the exercise instructions and is focused on the skills taught in the module.
- It may include common learner mistakes.
- If the explanation exceeds 7 minutes, it is broken into shorter videos at logical points.

#### Text Solution

Each video is paired with a **step-by-step written solution.**

- The solution summarizes the solution and is focused on the skills taught in the module.
- Key code snippets are included in the text, either in line or as separate code blocks.
- Common learner mistakes may be included in a **Common Mistakes to Avoid** section, even if they are not discussed in the video.

#### Solution Code/Artifacts

A complete author’s solution should be presented to help the learner review their work.

- For workspace exercises: the full solution should be available in a workspace on the page. Learners should be directed to the solution at the end of the solution summary.
- For local coding workspaces: a link to a GitHub repo containing the solution.
- For non-technical exercises: a full text or downloadable solution.

### Exercise Titles

Exercise titles should be descriptive and help learners remember what the exercise covers.
**Do not number exercises\!** Numbering conflicts with the classroom UI and our modular build strategy.
