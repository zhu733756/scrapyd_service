from scrapyd_api import ScrapydAPI
from scrapyd_api import constants
from scrapyd_api.compat import iteritems, urljoin

PULL_CODE_ENDPOINT = "/pullcode.json"
ADD_PROJECT_ENDPOINT = "/addproject.json"
PING_ENDPOINT = "/daemonstatus.json"
CRAWL_LOG_ENDPOINT = "/crawllog.json"


class DistributedScrapydApi(ScrapydAPI):

    def daemon_status(self):
        url = urljoin(self.target, PING_ENDPOINT)
        json = self.client.get(url, timeout=self.timeout)
        return json

    def add_version(self, project, version, egg):
        """
        Adds a new project egg to the Scrapyd service. First class, maps to
        Scrapyd's add version endpoint.
        """
        raise Exception("接口不支持")

    def crawl_log(self, cluser_node, project, spider,  job_id, show_total_log):
        '''
        get log on the cluster
        '''
        url = urljoin(self.target, CRAWL_LOG_ENDPOINT)
        data = dict(
            cluster_node=cluser_node,
            project=project,
            spider=spider,
            jobid=job_id,
            show_total_log=show_total_log
        )
        json = self.client.get(url, params=data, timeout=self.timeout)
        return json

    def pull_code(self, project=None):
        """
        pull code by git
        """
        url = urljoin(self.target, PULL_CODE_ENDPOINT)
        data = {
            'project': project,
        }
        json = self.client.post(url, data=data, timeout=self.timeout)
        return json

    def add_project(self, project):
        """
        push code by git
        """
        url = urljoin(self.target, ADD_PROJECT_ENDPOINT)
        data = {
            'project': project
        }
        json = self.client.post(url, data=data, timeout=self.timeout)
        return json

    def cancel(self, project, job, signal=None):
        """
        Cancels a job from a specific project. First class, maps to
        Scrapyd's cancel job endpoint.
        """
        url = self._build_url(constants.CANCEL_ENDPOINT)
        data = {
            'project': project,
            'job': job,
        }
        if signal is not None:
            data['signal'] = signal
        json = self.client.post(url, data=data, timeout=self.timeout)
        return json

    def delete_project(self, project):
        """
        Deletes all versions of a project. First class, maps to Scrapyd's
        delete project endpoint.
        """
        url = self._build_url(constants.DELETE_PROJECT_ENDPOINT)
        data = {
            'project': project,
        }
        json = self.client.post(url, data=data, timeout=self.timeout)
        return json

    def job_status(self, project, job_id):
        """
        Retrieves the 'status' of a specific job specified by its id. Derived,
        utilises Scrapyd's list jobs endpoint to provide the answer.
        """
        all_jobs = self.list_jobs(project)
        for state in constants.JOB_STATES:
            job_ids = [job['id'] for job in all_jobs[state]]
            if job_id in job_ids:
                return state
        return ''  # Job not found, state unknown.

    def delete_version(self, project, version):
        """
        Deletes a specific version of a project. First class, maps to
        Scrapyd's delete version endpoint.
        """
        raise Exception("接口不支持")

    def list_jobs(self, project):
        """
        Lists all known jobs for a project. First class, maps to Scrapyd's
        list jobs endpoint.
        """
        url = self._build_url(constants.LIST_JOBS_ENDPOINT)
        params = {'project': project}
        jobs = self.client.get(url, params=params, timeout=self.timeout)
        return jobs

    def list_projects(self):
        """
        Lists all deployed projects. First class, maps to Scrapyd's
        list projects endpoint.
        """
        url = self._build_url(constants.LIST_PROJECTS_ENDPOINT)
        json = self.client.get(url, timeout=self.timeout)
        return json['projects']

    def list_spiders(self, project):
        """
        Lists all known spiders for a specific project. First class, maps
        to Scrapyd's list spiders endpoint.
        """
        url = self._build_url(constants.LIST_SPIDERS_ENDPOINT)
        params = {'project': project}
        json = self.client.get(url, params=params, timeout=self.timeout)
        return json['spiders']

    def list_versions(self, project):
        """
        Lists all deployed versions of a specific project. First class, maps
        to Scrapyd's list versions endpoint.
        """
        raise Exception("接口不支持")

    def schedule(self, project, spider, settings=None, **kwargs):
        """
        Schedules a spider from a specific project to run. First class, maps
        to Scrapyd's scheduling endpoint.
        """

        url = self._build_url(constants.SCHEDULE_ENDPOINT)
        data = {
            'project': project,
            'spider': spider
        }
        data.update(kwargs)
        if settings:
            setting_params = []
            for setting_name, value in iteritems(settings):
                setting_params.append('{0}={1}'.format(setting_name, value))
            data['setting'] = setting_params
        json = self.client.post(url, data=data, timeout=self.timeout)
        return json
