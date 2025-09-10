import os
import yaml
from crewai import Agent, Task, Crew, Process, CrewBase, agent, task, crew
from typing import List

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")

def load_yaml(filename):
    with open(os.path.join(CONFIG_DIR, filename), "r") as f:
        return yaml.safe_load(f)

@CrewBase
class MediatorCrew():
    agents_config = load_yaml("agentcrews/mediator/config/agents.yaml")
    tasks_config = load_yaml("agentcrews/mediator/config/tasks.yaml")
    agents: List[Agent]
    tasks: List[Task]

    @agent
    def interpreter(self) -> Agent:
        return Agent(config=self.agents_config["interpreter"], verbose=True)

    @agent
    def planner(self) -> Agent:
        return Agent(config=self.agents_config["planner"], verbose=True)

    @agent
    def visualizer(self) -> Agent:
        return Agent(config=self.agents_config["visualizer"], verbose=True)

    @task
    def interpret_task(self) -> Task:
        return Task(config=self.tasks_config["interpret_task"])

    @task
    def plan_task(self) -> Task:
        return Task(config=self.tasks_config["plan_task"])

    @task
    def visualize_task(self) -> Task:
        return Task(config=self.tasks_config["visualize_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.interpreter(), self.planner(), self.visualizer()],
            tasks=[self.interpret_task(), self.plan_task(), self.visualize_task()],
            process=Process.sequential,
            verbose=True,
        )
