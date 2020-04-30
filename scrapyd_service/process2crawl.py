import pathlib
import sys
import os
from .utils import get_project_settings
from scrapy.crawler import CrawlerProcess
from scrapy.utils.misc import load_object
from tldextract import tldextract
import string
from copy import copy

underscore2bigHump = lambda name: ''.join(
    [i.capitalize() for i in name.split('_')])


def starturls2filename(url):
    domain_val = tldextract.extract(url)
    s = domain_val.subdomain
    d = domain_val.domain
    sx = domain_val.suffix
    return f"{s}_{d}_{sx}".replace('.', '_')


def get_project_template(project, version=None):
    '''如果版本号是空,则取时间戳最大的一个template文件'''
    project_template_path = templates_path.joinpath(project)
    if not project_template_path.exists():
        raise FileNotFoundError(f"文件路径{str(project_template_path)}不存在")
    if version is None:
        version = max([int(x.name.split(".")[0])
                       for x in project_template_path.iterdir()
                       if x.name.split(".")[0].isdigit() and x.name.endswith("tmpl")])
    version_path = project_template_path.joinpath(f"{version}.tmpl")
    if not version_path.exists():
        raise FileNotFoundError(f"文件路径{str(version_path)}不存在")
    return str(version_path)


def load_spiderCls(**spkwargs):
    '''
    功能:读取template,渲染后生成spider,并返回相对路径给load_object读取类文件
    args:force_build,bool,是否强制覆盖
    '''
    kwargs = copy(spkwargs)
    start_urls = kwargs.pop("start_urls")
    article_rule = kwargs.pop('article_rule')
    spider_name = kwargs.pop("name")
    file_name = starturls2filename(url=start_urls[0])
    capfilename = underscore2bigHump(name=file_name)
    project = kwargs.pop("project")
    force_build = kwargs.get("force_build", False)
    render_project_path = spiders_path.joinpath(f"{project}")
    if not pathlib.Path(render_project_path).exists():
        os.makedirs(render_project_path)
    render_spider_path = render_project_path.joinpath(file_name + ".py")
    if force_build or not pathlib.Path.exists(render_spider_path):
        project_template_path = get_project_template(
            project, kwargs.get("version", None))
        with open(project_template_path, 'rb') as fp:
            raw = fp.read().decode('utf8')
        content = string.Template(raw).substitute(
            capfilename=capfilename,
            name=spider_name,
            article_rule=article_rule,
            allowed_domains=kwargs.get('allowed_domains'),
            start_urls=start_urls)
        with open(str(render_spider_path), 'wb') as file:
            file.write(content.encode('utf8'))
    path = f".spiders.{project}.{file_name}.{capfilename}Spider"
    return load_object(path=path)