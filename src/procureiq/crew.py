from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.tools import BaseTool
from typing import List, Optional
import os
from geopy.geocoders import Nominatim  # type: ignore
import requests

# Custom tool for geolocation using Nominatim
class GeolocationTool(BaseTool):
    name: str = "GeolocationTool"
    description: str = "A tool to get geolocation data using Nominatim."

    def _run(self, query: str) -> dict:
        geolocator = Nominatim(user_agent="procureiq-agent")
        location = geolocator.geocode(query)
        if location:
            return {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "address": location.address
            }
        return {"error": "Location not found"}

# Custom tool for API requests
class APITool(BaseTool):
    name: str = "APITool"
    description: str = "A tool to make HTTP requests to any API endpoint."

    def _run(self, url: str, params: Optional[dict] = None) -> dict:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class Procureiq:
    """Procureiq crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def rfx_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['rfx_generator'], # type: ignore[index]
            verbose=True
        )
    
    @agent 
    def supplier_finder(self) -> Agent:
        try:
            config = self.agents_config['supplier_finder']
        except KeyError:
            raise ValueError("configuration for supplier_finder not found in agents.yaml")
        return Agent(
            config=config,
            verbose=True,
        )
    
    @agent
    def negotiation_strategist(self) -> Agent:
        # Initialize custom tools
        geolocation_tool = GeolocationTool()
        api_tool = APITool()

        return Agent(
            config=self.agents_config['negotiation_strategist'], # type: ignore[index]
            verbose=True,
            tools=[
                geolocation_tool,  # Geolocation & Coverage Intelligence
                api_tool,          # Currency Exchange Rates and Supplier Risk
            ]
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def rfx_generator_task(self) -> Task:
        return Task(
            config=self.tasks_config['rfx_generator_task'], # type: ignore[index]
            output_file="rfx.md"
        )
    
    @task
    def supplier_finder_task(self) -> Task:
        return Task(
            config=self.tasks_config['supplier_finder_task'],
            output_file="suppliers.csv"
        )
    
    @task
    def negotiation_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config['negotiation_strategy_task'],
            output_file="negotiation_strategy.md",
            dependencies=[self.supplier_finder_task]  # Depends on suppliers.csv
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Procureiq crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )