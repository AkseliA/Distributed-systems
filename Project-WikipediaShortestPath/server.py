import sys
from time import perf_counter
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from socketserver import ThreadingMixIn
import requests
from collections import deque  # https://stackoverflow.com/a/717261
from concurrent.futures import ThreadPoolExecutor, as_completed

# Timeout value to prevent excessive long queries
TIMEOUT = 360


class Search:
    def __init__(self, start, end, path, path_found, timeout):
        self.start = start
        self.end = end
        self.path = path
        self.path_found = path_found
        self.timeout = timeout


# Creates threads for clients
class ThreadedSimpleXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/t2",)


# https://www.jcchouinard.com/wikipedia-api/#Find_all_links_on_the_page
# https://www.mediawiki.org/wiki/API:Links
def extract_links(page, search):
    if(search.path_found or search.timeout):
        return

    links = []
    URL = "https://en.wikipedia.org/w/api.php"
    PARAMS = {"action": "query", "titles": page,
              "prop": "links", "format": "json", "pllimit": "max"}
    try:
        # The following query returns max 500 links (pllimit). If the page contains more links the response contains "continue",
        # which is used to fetch the remaining links.
        session = requests.Session()
        response = session.get(url=URL, params=PARAMS)
        try:
            data = response.json()
            pages = data["query"]["pages"]
            for key, value in pages.items():
                for link in value["links"]:
                    if(link["ns"] == 0):  # Only append links from "main" namespace (ns)
                        links.append(link["title"])
            # Fetch the remaining links until no "continue" parameter in response
            while "continue" in data:
                PARAMS["plcontinue"] = data["continue"]["plcontinue"]
                response = session.get(url=URL, params=PARAMS)
                data = response.json()
                pages = data["query"]["pages"]
                for key, value in pages.items():
                    for link in value["links"]:
                        if(link["ns"] == 0):  # Only append links from "main" namespace (ns)
                            links.append(link["title"])

        except Exception as e:  # No links
            pass

    except requests.exceptions as e:
        print(e)

    return links


class RpcFunctions:
    # Check if endpoints are valid wikipedia pages
    # Additionally check if end page is accessable through links
    def validate_endpoint(self, endpoint, checkLeadingLinks):
        try:
            res = requests.get(f"https://en.wikipedia.org/wiki/{endpoint}")
            if(res.status_code == 200):  # Valid article
                if(checkLeadingLinks):

                    session = requests.Session()
                    response = session.get(url="https://en.wikipedia.org/w/api.php",
                                           params={"action": "query", "bltitle": endpoint, "list": "backlinks", "format": "json"}).json()
                    if not response["query"]["backlinks"]:
                        return False

                return True
            elif (res.status_code != 200):
                return False
        except requests.exceptions.RequestException as e:
            print(e)
            return False

    # https://github.com/stong1108/WikiRacer/blob/master/wikiracer.py
    # https://docs.python.org/3/library/concurrent.futures.html
    def breadth_first_search(self, start, end):
        search = Search(start, end, [], False, False)
        timeStart = perf_counter()
        # Dictionary for holding found paths {pageTitle: [path_to_it]}
        path = {}
        path[start] = [start]
        queue = deque([start])  # Double-ended queue of pages to visit

        # Runs until path is found or timeout (360s)
        while not search.path_found:
            with ThreadPoolExecutor(max_workers=None) as executor:
                futures = {}
                while queue:
                    if not search.path_found:
                        page = queue.popleft()
                        futures[executor.submit(
                            extract_links, page, search)] = page

                print(f"Threads in use: {len(executor._threads)}")
                for future in as_completed(futures):
                    page = futures[future]
                    links = future.result()

                    if (perf_counter() - timeStart) > TIMEOUT:  # Check if timeout value is passed
                        search.timeout = True
                        print(f"Timeout value {TIMEOUT} exceeded")
                        return {"success": False, "msg": f"Timeout error, search exceeded {TIMEOUT} sec"}

                    if links:
                        for link in links:

                            # Path found -> return the path to client and send termination signal to other threads (search.path_found)
                            if(link.casefold() == end.casefold()):
                                timeEnd = perf_counter()
                                totalTime = round(timeEnd - timeStart, 1)
                                print(
                                    f"Path found in: {totalTime} sec")
                                search.path_found = True
                                search.path = path[page] + [link]
                                return {"success": True, "path": search.path, "time": totalTime}

                            if link not in path and link != page:
                                path[link] = path[page] + [link]
                                queue.append(link)


def main():

    with ThreadedSimpleXMLRPCServer(("127.0.0.1", 8000), requestHandler=RequestHandler) as rpcserver:
        rpcserver.register_introspection_functions()  # Default functions
        rpcserver.register_instance(RpcFunctions())  # Own functions

        try:
            print("server running on '127.0.0.1:8000'")
            rpcserver.serve_forever()

        except KeyboardInterrupt:
            print("Shutting down...")
            sys.exit(0)


if __name__ == '__main__':
    main()
