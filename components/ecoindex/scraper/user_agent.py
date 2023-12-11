from random_user_agent.params import OperatingSystem, SoftwareName
from random_user_agent.user_agent import UserAgent


async def get_user_agent() -> str:
    software_names = [SoftwareName.CHROME.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]

    user_agent_rotator = UserAgent(
        software_names=software_names, operating_systems=operating_systems, limit=100
    )

    return user_agent_rotator.get_random_user_agent()
