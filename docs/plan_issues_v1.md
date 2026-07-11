# .agent-tasks/architect/PLAN.md changes:

- I've already setup terraform, configured aws cli, initialized the git repo, and verified all tools as per the @docs/PREREQUISITES.md file.
- In Phase 1 add a step after locking TDD to ensure the tests fail. Then, continue the steps as usual.
- in phase 2 do I need to do anything on the console for IAM roles, or can it be done via cli? And what does the destroy workflow cover?
- In phase 3, resolve ambiguity, whether lambda api or direct sdk. Will this clash with the intent to try the different invokers? I.e. EC2, ECS/Fargate, and lambda?
- In phase 3, evaluate whether the annotation rendering logic needs manual implementation or if Canvas does it on its own, and whether I need to do any setup for Canvas.
- In phase 4 EC2 worker deployment and Phase 5 ECS/Fargate + CI/CD, are they going to be substitutable? Are they supposed to work together? I need you to reconfirm that you are clear we're designing the architecture with substitutable process workers, and how your plan allows for it or takes care of it.
- Let's put the documentation by the technical writer closer to the beginning of the project, once the architectural decisions are finalized. The final phase 7 documentation should just update or correct things based on decision changes during development. For cost comparison docs maybe have the @util/research-analyst do the research necessary. We have the @util/codebase-doc sub-agent to create codebase documentation, and that can only be done near the end so we leave that in phase 7.
- Under 'Key Design Decisions' it's clear that CI+CD will be iterative, v1 being docker image, v2 being tf, v3 being frontend, but the design phases only seem to mention 2 versions for ci/cd, is this a mistake?

# app/tester PLAN.md:

- Remove the 'optionally refractor both test and implementation', the tester only writes and runs tests. They don't refractor anything.
- The workflow allows for ambiguity. Change so that it runs all locked tests once written, confirms they all fail because implementation code doesn't exist yet, and then signal the orchestrator as already mentioned. Then, it just waits until the orchestrator re-invokes it after the necessary code is implemented, so the tester needs to run the tests again and confirm which are passing and which fail.

# ml/data-engineer PLAN.md:

- The comment on line 16 for the bbox schema is wrong; YOLO uses [x_center, y_center, width, height] with normalized values for coordinates. COCO used [x1, y1, x2, y2].

# app/backend-dev PLAN.md:

- Don't leave ambiguity to the backend developer, between implementation options. As discussed, we go with the Lambda function + API gateway for the API implementation, task 3.8. Remove the ambiguity there.

# app/technical-writer PLAN.md:

- Architecture diagram can just be Mermaid in the README + Excalidraw file, since excalidraw uses json which is more agent-friendly than draw.io's XML format.
- These agents can't use screenshots, so stick to command snippets for 7.3 deployment guide.
