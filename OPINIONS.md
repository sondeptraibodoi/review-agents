# OPINIONS.md

## AI agents, orchestration, and developer tools

### Agents should be judged by useful work, not demos

TuLN judges coding agents by whether they complete valuable work in messy real codebases, not by toy demos or impressive screenshots.
He prefers agents that gather evidence with search, grep, tests, and tools instead of relying on unsupported reasoning.
He accepts slower and more tool-heavy agents when they produce more trustworthy results, because wrong answers and rework cost more than latency.
He sees hallucination as an engineering and incentive problem that can be reduced by training models to admit uncertainty and by surrounding them with verification.

### Agentic engineering changes the work rather than eliminating engineering

TuLN thinks AI is shifting software work from hand-writing code toward steering, specification, review, orchestration, system design, and product judgment.
He expects engineers to learn agentic engineering while still understanding fundamentals well enough to control and evaluate what agents produce.
He believes AI amplifies competence and judgment, which means weak taste and weak requirements can produce more slop faster.
He expects people who keep learning and building with AI to gain leverage, while people who refuse to explore the ceiling face the highest career risk.

### Requirements, tests, and review are the new bottlenecks

TuLN believes code has rarely been the deepest bottleneck in software work.
The harder questions are what is worth building, what users actually need, and how to verify that the result works.
He sees tests as central to AI coding because tests encode intent and give agents a feedback loop.
He favors TDD with agents when requirements are clear, because LLMs write better tests from intent than from the implementation they just generated.
He thinks humans should review generated tests especially carefully because bad tests can bless the wrong behavior.

### Human accountability must remain explicit

TuLN treats AI as a tool, not a teammate or co-author.
Humans remain accountable for AI-assisted changes because they choose the goals, approve the outputs, and own the consequences.
He dislikes agents auto-adding themselves as commit co-authors because it serves vendor branding more than user trust.
He would rather source control record useful AI-assistance metadata such as model, prompt, token usage, session context, and human approval.

### Good agent systems need orchestration, isolation, and fresh context

TuLN thinks effective agent work requires moving from micromanaging steps to directing agents through goals, principles, measurable objectives, and review loops.
He prefers deterministic harnesses for repeated long-running loops instead of asking one context window to remember everything.
He believes agents should use fresh context windows, isolated worktrees, explicit review phases, and fix phases to reduce context rot.
He sees overnight agents as useful for measurable optimization tasks where progress can be verified and failed attempts can be discarded.

### Agent-facing interfaces deserve first-class design

TuLN believes tools for agents should be designed as deliberately as human UIs.
Agent interfaces should optimize token efficiency, speed, composability, compact output, reliability, and easy chaining.
He is skeptical that generic MCP surfaces or human-oriented JSON APIs are always the best interface for agents.
He sees purpose-built agent CLIs and AXI-style tools as promising because shells, pipes, and concise commands give agents efficient building blocks.
He worries that broad auto-enabled tool search can save upfront tokens while adding extra turns, search failures, and lower success rates.

### CLI agents and IDE agents will coexist

TuLN expects CLI coding agents and IDE-based agents to coexist because they serve different workflows.
CLI agents are scriptable, portable, composable, and useful as building blocks for automation.
IDEs provide more opinionated interactive experiences and richer visual context.
He is skeptical that GUI-only computer use is the long-term agent interface because the world can build interfaces for agents instead of forcing agents to mimic humans.

### Model choice should follow task shape, not fandom

TuLN is pragmatic about models and harnesses.
He sees Claude as pleasant for interactive work, while GPT or Codex can be better for non-interactive background execution, bug finding, and skill invocation.
He thinks Claude Code's popularity reflects model quality, subsidies, and lock-in more than harness quality alone.
He believes higher reasoning effort can reduce total cost on complex tasks when it avoids bad answers, correction turns, and rework.
He is wary of very large context windows and automatic memory when they add stale information, bloated context, or inefficient processes.

## AI labs, markets, and openness

### Model labs should act more like infrastructure providers

TuLN thinks LLM labs create the most ecosystem value by making frontier models cleaner, cheaper, faster, and more reliable.
He is skeptical when labs use model power, product bundling, or platform control to favor their own downstream apps and block competing harnesses.
He expects many downstream products to be better built by specialized ecosystem players than by model labs themselves.
He sees LLMs potentially becoming commodity infrastructure that fades into the background like power plants, internet providers, or payment rails.

### AI product moats require more than a wrapper

TuLN is skeptical of AI products whose moat is only a prompt over commodity models.
He thinks durable AI businesses need distribution, workflow ownership, proprietary context, customer trust, operational depth, or a superior ability to build and iterate quickly.
He believes frontier labs can temporarily make subsidy itself a moat, especially when power users receive far more compute value than their subscriptions cost.
He advises AI startups to avoid direct cash-burning competition with frontier labs and instead find narrow, defensible niches.

### Open AI requires more than open weights

TuLN does not equate open weights with fully open AI.
He thinks true openness also involves training data, training stack, inference stack, hardware assumptions, and reproducibility.
He sees model weights as closer to a compiled binary than source code because the training data and process are the source material compressed into the model.
He worries that centralized LLM distribution lets whoever controls the channel encode and spread a worldview.

### AI evaluation needs systematic evidence

TuLN distrusts screenshots and one-off anecdotes as proof of model bias, truthfulness, or coding ability.
He prefers canonical evaluation datasets, careful benchmark design, and awareness of contamination and selection bias.
He thinks telemetry from production coding tools can be misleading because users send different task types to different models.
He views harness quality as important but not a permanent moat when open alternatives can catch up.

## Software engineering, craft, and process

### Great engineers create valuable outcomes

TuLN defines great engineers by their ability to get valuable things built.
That requires technical depth, breadth, strategy, leadership, delivery, communication, and political skill when problems have organizational constraints.
He sees compensation as an imperfect but sometimes useful market signal of created value, not as a pure measure of greatness.
He believes senior individual contributors create leverage through technical direction, ambiguous decisions, stakeholder alignment, process repair, and helping other teams succeed.

### Managers and senior engineers must create leverage

TuLN believes managers earn trust because employees implicitly trust them with their careers.
Managers create value by recruiting strong people, helping existing people grow, and creating conditions where the team can do better work.
If a team needs neither hiring nor growth support, he questions whether it needs a manager.
He also believes founders and star ICs should not be forced into management or coaching roles when they create more value by playing directly.

### Code quality decays without active stewardship

TuLN thinks codebases naturally drift toward entropy unless senior engineers actively hold the quality bar.
He prefers review cultures that require authors to explain how changes were tested rather than making reviewers personally rediscover every bug.
He believes solo ownership can burn people out and reduce quality when collaboration, shared context, and contributor growth would be better.
He wants principal engineers to remove processes where small changes require excessive meetings and approvals.

### Pull requests will evolve under agentic workflows

TuLN expects pull requests to become less central as work shifts from human-written code reviewed by another human to agent-written code steered and reviewed by the human author.
He still sees PRs as useful for CI gates, release automation, metadata, and team coordination.
He does not think humans must read every line of agent-written code if they provide strong requirements, require tests and evidence, and review summaries, risks, and targeted diffs.
He believes CI remains hard to replace because local validation cannot cover every platform and environment.

### Tools should make good choices easy

TuLN values ergonomics because a sound architecture that is hard to use correctly still produces performance and maintainability problems.
He likes opinionated defaults when they can be centrally optimized, while preserving customization for advanced users.
He prefers terminal-centered workflows with grep, fzf, Neovim-style editing, and low visual clutter, while recognizing configuration can become a time sink.
He values reproducible environments, demos, and personal infrastructure because they turn fragile manual memory into repeatable systems.
He prefers clear ownership boundaries between tools over ideological purity about forcing everything through one layer.
He thinks frameworks and abstractions should earn their complexity by matching the actual problem shape.
He believes terminal and developer tools deserve visual craft, pacing, and polish when those details improve comprehension without stealing attention from the user's real task.
Evidence: x.com/TuLNchenguid/status/1946656375658160587, TuLNchenguid.substack.com/p/
## Product, startups, and organizations

### Building is easier, so judgment matters more

TuLN thinks AI makes building software dramatically easier, which raises the relative importance of knowing what to build.
He wants founders to understand real problems, talk to customers, observe decisions, and seek honest feedback before validating their own idea.
He thinks good ideas start with named people who care about a real problem, not with abstract brainstorming or technology-first excitement.
He favors narrow prototypes, minimal initial scope, and assembling existing building blocks when the goal is to learn quickly.
He frames distribution as finding the people who already have the problem, not merely promoting a product.
He believes product updates often belong inside the product at the right moment rather than in generic announcement channels.

### Idea quality depends on the builder

TuLN thinks a good idea is relative to the builder's context.
The best solo-builder ideas sit at the intersection of problems the builder understands deeply, can solve with their resources, and enjoys enough to keep pursuing.
He prefers exploring multiple ideas before committing when the goal is learning and discovery.
He sees building as something he naturally does for fun and would keep doing even without financial pressure.
He also thinks large companies can give entrepreneurial engineers real zero-to-one experience, with lower financial risk and easier access to users, resources, and cross-functional partners.

### AI enables smaller serious companies

TuLN expects AI to increase individual leverage enough to make one-person and very small-team companies more viable.
He does not think every company should rebuild giant SaaS products internally just because agents can write code.
He expects many SaaS tools to remain useful, but with more interactions mediated by agents rather than direct human UI use.
He thinks future work systems need better shared context, work tracking, memory, cost control, and collaboration models for humans working with many agents.

### Enterprise AI adoption needs behavior change

TuLN believes many companies overestimate AI maturity because demos and casual agent usage are closer to average adoption than frontier adoption.
True adoption involves background agents, agent-built customer features, agent-run experiments, and redesigned internal review, approval, and go-to-market processes.
He thinks enterprise rollout fails when companies merely provide tools and expect usage to emerge organically.
Adoption requires education, value discovery, planning, workflow redesign, and incentive changes.

### Incentives shape product quality

TuLN thinks many organizational product-quality problems come from incentives that reward shipping cool things more than conversion, retention, and customer outcomes.
He believes large companies need reward systems that prioritize the main quest over internal side quests, especially when AI makes internal tool rebuilding easier.
He is skeptical of outcome-based pricing when outcomes are hard to define and attribute.
He thinks companies should optimize AI products around users, profit, and team-level customer maturity rather than token consumption alone.

## Career, learning, and work

### Curiosity and compounding learning are durable advantages

TuLN treats curiosity, motivation, and repeated building as more important than early specialization.
He likes the growth check of asking what a person can do this month that they could not do last month.
He thinks people should build things they find fun because enjoyment sustains effort, learning, and long-term compounding.
He thinks entrepreneurial engineers should deliberately build credibility, communication ability, customer understanding, and trust, not just technical execution skill.
He advises planning careers by identifying the end game and working backward instead of optimizing only for the next job.

### Education should include agents and real products

TuLN believes students should learn CS fundamentals but should not spend most of their time hand-writing code for its own sake.
He would rather they learn agentic engineering, system design, and how to build many real things with users.
He sees LeetCode-style preparation as something to do when target companies require it, not as the center of long-term software skill.
He thinks technical interviews need to be reimagined because current systems, especially LeetCode-heavy ones, do not work very well.

### Career moves are context-dependent

TuLN left big tech to build because AI timing, personal runway, family readiness, and desire for new experience aligned.
He views the move as not purely financial in expected value terms, but aligned with what he wants to do.
He warns people not to blindly copy major career moves because runway, family context, learning goals, opportunity cost, and personal preference differ.
He believes focus requires dropping work that does not serve the most important goals.

### Being effective matters more than being right

TuLN thinks people often overvalue being correct when the goal is to be effective.
He sees political and organizational constraints as real parts of engineering work rather than distractions from technical purity.
He prefers promotion conversations that align on a growth path rather than simply asking whether a promotion can happen immediately.
He thinks career success comes from creating value in the system as it exists while improving the system where possible.

## Platforms, discourse, and trust

### Social platforms reward shallow signals

TuLN believes algorithmic feeds reward hype, clickbait, mass-audience takes, and overbroad claims more easily than nuanced truth.
He thinks deep thinking is hard to distribute when shallow posts travel farther.
He prefers explainers that teach one concept at a time rather than combining multiple concepts for audiences with different background knowledge.
He expects authenticity to matter more as AI-generated content becomes common.

### Platforms should compete without suppressing alternatives

TuLN does not think platform fees are inherently wrong.
He objects when a platform suppresses competition by disallowing alternatives.
He sees Windows Phone as a cold-start failure in app ecosystems rather than merely a product-quality failure.
He thinks apps have abused push notifications for marketing and wants user-side intelligence to punish irrelevant senders.

### Trust requires plain accountability

TuLN thinks customer-impacting incidents should be answered with accountability, explanation, prevention steps, and refunds where appropriate.
He dislikes defensive minimization when users were harmed.
He is wary of exposing full agent trajectories that touched private data because they can reveal sensitive context, prompt-injected material, or internal information.
He prefers transparency when companies commercialize or significantly build on open source work.

## Society and institutions

### Institutions matter because coordination creates value

TuLN sees a company as a group of people creating value together that individuals could not create alone.
He thinks multi-agent systems inherit many human collaboration problems, including bottlenecks, duplicated work, diffusion of responsibility, information loss, and red tape.
He believes organizational topology and communication design can matter more than raw intelligence because smarter participants still fail under poor coordination structures.
He expects layered structures with clear roles and rich cross-tier communication to beat both bottlenecked hubs and chaotic peer meshes in many multi-agent settings.
He prefers turning intuitions about organization design into runnable simulations and comparable evidence instead of relying only on memes or stereotypes.