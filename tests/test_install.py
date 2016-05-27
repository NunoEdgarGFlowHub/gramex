import os
import shutil
import unittest
from pathlib import Path
from shutilwhich import which
from orderedattrdict import AttrDict
from six.moves.urllib.parse import urljoin
from gramex.config import variables, PathConfig
from gramex.install import install, uninstall, run
from . import server

folder = os.path.dirname(os.path.abspath(__file__))


class TestInstall(unittest.TestCase):
    zip_url = urljoin(server.base_url, 'install-test.zip')
    zip_file = os.path.join(folder, 'install-test.zip')

    @staticmethod
    def appdir(appname):
        return os.path.abspath(os.path.join(variables['GRAMEXDATA'], 'apps', appname))

    def check_files(self, appname, expected_files):
        '''app/ directory should have expected files'''
        folder = self.appdir(appname)
        actual = set()
        for root, dirs, files in os.walk(folder):
            for filename in files:
                if '.git' not in root:
                    actual.add(os.path.join(root, filename))
        expected = {os.path.abspath(os.path.join(folder, filename))
                    for filename in expected_files}
        self.assertEqual(actual, expected)

        conf = +PathConfig(Path(self.appdir('apps.yaml')))
        self.assertTrue(appname in conf)
        self.assertTrue('target' in conf[appname])
        self.assertTrue('cmd' in conf[appname] or 'url' in conf[appname])
        self.assertTrue('installed' in conf[appname])
        self.assertTrue('time' in conf[appname].installed)


    def check_uninstall(self, appname):
        '''Check that appname exists. Uninstall appname. It should be removed'''
        folder = self.appdir(appname)
        self.assertTrue(os.path.exists(folder))
        uninstall([appname], {})
        self.assertFalse(os.path.exists(folder))

    def check_zip(self, appname, files, **params):
        '''Test installing and uninstalling a zipfile via URL and as a file'''
        args = AttrDict(params)
        for url, suffix in ((self.zip_url, '-url'), (self.zip_file, '-file')):
            args.url = url
            subappname = appname + suffix
            install([subappname], args)
            self.check_files(subappname, files)
            self.check_uninstall(subappname)

    def test_zip(self):
        self.check_zip('zip', files={
            'dir1/dir1.txt', 'dir1/file.txt', 'dir2/dir2.txt', 'dir2/file.txt'})

    def test_zip_rootdir(self):
        self.check_zip('zip-dir1', rootdir='dir1', files={'dir1.txt', 'file.txt'})
        self.check_zip('zip-dir2', rootdir='dir2', files={'dir2.txt', 'file.txt'})

    def test_zip_url_contentdir(self):
        self.check_zip('zip-contentdir', contentdir=False, files={
            'common-root/dir1/dir1.txt', 'common-root/dir1/file.txt',
            'common-root/dir2/dir2.txt', 'common-root/dir2/file.txt'})

    def test_zip_flat(self):
        install(['zip-flat'], AttrDict(url=urljoin(server.base_url, 'install-test-flat.zip')))
        self.check_files('zip-flat', ['file1.txt', 'file2.txt'])
        self.check_uninstall('zip-flat')

    def test_dir(self):
        dirpath = os.path.join(folder, 'dir', 'subdir')
        install(['dir'], AttrDict(url=dirpath))
        self.check_files('dir', os.listdir(dirpath))
        self.check_uninstall('dir')

    def test_dir(self):
        dirpath = os.path.join(folder, 'dir', 'subdir')
        install(['dir'], AttrDict(url=dirpath))
        self.check_files('dir', os.listdir(dirpath))
        self.check_uninstall('dir')

    def test_git_url(self):
        git_files = ['dir1/file.txt', 'dir1/file-dir1.txt', 'dir2/file.txt', 'dir2/file-dir2.txt']
        git_url, branch = 'http://code.gramener.com/s.anand/gramex.git', 'test-apps'

        cmd = 'git clone %s --branch %s --single-branch' % (git_url, branch)
        install(['git-url'], AttrDict(cmd=cmd))
        self.check_files('git-url', git_files)

        cmd = 'git clone %s $TARGET --branch %s --single-branch' % (git_url, branch)
        install(['git-url'], AttrDict(cmd=cmd))
        self.check_files('git-url', git_files)

        # Note: Deleting .git directory fails, so lets not bother for now
        # self.check_uninstall('git-url')

    def test_setup(self):
        dirpath = os.path.join(folder, 'dir', 'install')
        install(['setup'], AttrDict(url=dirpath))

        result = set()
        for root, dirs, files in os.walk(dirpath):
            for filename in files:
                path = os.path.join(root, filename)
                result.add(os.path.relpath(path, dirpath))

        if which('powershell'):
            result.add('powershell-setup.txt')
        if which('make'):
            result.add('makefile-setup.txt')
        if which('bash'):
            result.add('bash-setup.txt')
        if which('python'):
            result.add('python-setup.txt')
        if which('npm'):
            result.add('node_modules/gramex-npm-package/package.json')
            result.add('node_modules/gramex-npm-package/npm-setup.js')
        if which('bower'):
            result.add('bower_components/gramex-bower-package/bower.json')
            result.add('bower_components/gramex-bower-package/bower-setup.txt')
            result.add('bower_components/gramex-bower-package/.bower.json')
        self.check_files('setup', result)
        self.check_uninstall('setup')