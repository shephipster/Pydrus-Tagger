# This will do the following
# 1) Connect to HydrusAPI
# 2) Fetch anything with a nhentai url
# 3) Group images with the same url
# 4) Fetch all the title tags, apply to all images in the group

import Hydrus.HydrusApi as HydrusApi

def health_checker():
    #Checks to see if everything works before even bothering. Will inform the user of any issues
    #check can connect to Hydrus
    status = HydrusApi.test_connection()
    if status != 200:
        return "Failed to connect to the Hydrus Client"
    #check can get tags
    status = HydrusApi.test_fetch()
    if status != 200:
        return "System could not fetch files from the Hydrus Client"
    #check can add tags
    #check can remove tags (not actually really needed, just want to remove the tag added previously)
    status = HydrusApi.test_tags()
    if status != 200:
        return "Could not add or remove tags on the Hydrus client"
    return "Success"

def unique_urls(source_url:str):
    # search all images with site:domain
    # group by url
    results = HydrusApi.groupByUrl(source_url)
    results = results.json()
    return results

def operate_by_site(site:str):
    encoded_site = f'site:{site}'
    results = HydrusApi.getHashesFromHydrus(encoded_site)
    return results

def get_group_urls(source_url:str):
    from time import sleep
    group_hashes = operate_by_site(site=source_url)
        
    # for each hash in group_hashes
    while group_hashes:
        hash = group_hashes[0]
        metadata = HydrusApi.getMetaFromHash(hash)
        known_urls = metadata['known_urls']
        for url in known_urls:
            group_data = unique_urls(url)
            group_size = len(group_data['url_file_statuses'])
            if group_size > 1:  #don't want to count the url if it was just the url of a page and not a gallery/group
                group = [hash['hash'] for hash in group_data['url_file_statuses']]
                for hash in group:
                    try:
                        group_hashes.remove(hash)
                    except:
                        # somehow already removed, chance it got doubled up
                        pass
                combine_group_namespaces(group)
                # give hydrus a few seconds to chill
                sleep(3)
                
    
def combine_group_namespaces(group:list):
    metadata = HydrusApi.getMetaFromHashes(*group)
    all_known_namespace_tags = set()
    namespace_tags = [r'title:', 'creator:', 'title full:', 'title jp:']
    for file in metadata:
        for group_id in file['tags']:
            tag_data = file['tags'][group_id]['display_tags']['0'] if file['tags'][group_id]['display_tags'] else []
            for tag in tag_data:
                for namespace_tag in namespace_tags:
                    if namespace_tag in tag:
                        all_known_namespace_tags.add(tag)
        
    #add namespace tags to local tags
    print(all_known_namespace_tags)
    for hash in group:
        HydrusApi.addTagsByHash(hash, list(all_known_namespace_tags))
        
    HydrusApi.addHashesToPage('Site Condensor', *group)
    return metadata
    
get_group_urls('nhentai.net')