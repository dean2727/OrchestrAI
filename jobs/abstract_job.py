from abc import ABC, abstractmethod

class AIJob(ABC):
    @abstractmethod
    def run(self):
        """Run the job logic."""
        pass

    @abstractmethod
    def get_command(self):
        """
        Return the command that will be executed in the container for this job.
        For example: "python -m jobs.bible_notification_job_runner"
        """
        pass

    @abstractmethod
    def get_job_name(self):
        """Return a unique job name identifier."""
        pass