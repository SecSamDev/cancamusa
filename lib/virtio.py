import wget

class VirtioDownloader:
    def download_virtio(output_path, virtio_version):
        pattern_virtio = re.compile('(\\d\\.\\d\\.\\d{2,3})(?:-(\\d)){0,1}', re.MULTILINE)
        virtio_match = re.search(pattern_virtio, virtio_version)
        virtio_version = virtio_version
        virtio_subversion = 1
        if virtio_match and len(virtio_match.groups()) == 2:
            virtio_version = virtio_match.groups()[0] or '0.1.172'
            virtio_subversion = virtio_match.groups()[1] or 1
            download_url = 'https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/archive-virtio/virtio-win-{virtio_version}-{virtio_subversion}/virtio-win-{virtio_version}.iso'.format(virtio_version=virtio_version, virtio_subversion=virtio_subversion)
            virtio_cache_location = os.path.join(output_path, 'virtio-win-{virtio_version}-{virtio_subversion}.iso').format(
            virtio_version=virtio_version, virtio_subversion=virtio_subversion)
            print('Downloading Virtio drivers {virtio_version}-{virtio_subversion} from:'.format(virtio_version=virtio_version, virtio_subversion=virtio_subversion))
            print(download_url)

        else:
            download_url = "https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso"
            virtio_cache_location = os.path.join(output_path, 'virtio-win-stable.iso')
            print('Downloading Virtio drivers {virtio_version}-{virtio_subversion} from:'.format(virtio_version=virtio_version, virtio_subversion=virtio_subversion))
            print(download_url)
            

        if not os.path.isfile(virtio_cache_location):
            if not os.path.isdir(output_path):
                os.makedirs(output_path)
            wget.download(download_url, virtio_cache_location)
        else:
            print('Reading drivers from cache at {virtio_cache_location}'.format(irtio_cache_location=virtio_cache_location))
        return virtio_cache_location
