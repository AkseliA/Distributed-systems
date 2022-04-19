# https://docs.python.org/3/library/xmlrpc.client.html#module-xmlrpc.client
import xmlrpc.client


rpcServer = xmlrpc.client.ServerProxy("http://127.0.0.1:8000/t2")


def validateEndpoint(endpoint, checkLeadingLinks):
    res = True
    try:
        if(not rpcServer.validate_endpoint(endpoint, checkLeadingLinks)):
            print(f"Error: '{endpoint}' not valid wikipedia article\n")
            res = False

    except xmlrpc.client.Fault as e:
        print("Error occured, please try again.")
        res = False

    return res


def breadthFirstSearch(start, end):
    try:
        res = rpcServer.breadth_first_search(start, end)
        if(res["success"]):
            print(f"\nPath found in {res['time']} seconds.\nPath: ", end="")
            print(*res["path"], sep=" -> ", end="\n\n")

        elif(not res["success"]):
            print(res["msg"])

    except xmlrpc.client.Fault as e:
        print("Error occured, please try again.")


def main():
    print("-------------------------------------",
          "\n|      Wikipedia shortest path      |",
          "\n-------------------------------------",
          "\nAn app for finding paths between two wikipedia articles")

    while(True):
        start = input("From: ")
        end = input("To: ")

        if(start and end and start != end):  # Check if endpoints are valid wikipedia articles
            print("\nValidating endpoints...")
            if(validateEndpoint(start, False) and validateEndpoint(end, True)):
                # Endpoints are valid -> start bfs algorithm
                print(f"Success\nStarting BFS from '{start}' to '{end}'")
                breadthFirstSearch(start, end)
                break

        else:
            print("\nInvalid choice, try again.")


if __name__ == '__main__':
    main()
