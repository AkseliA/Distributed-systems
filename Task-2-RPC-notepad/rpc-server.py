# https://docs.python.org/3/library/xmlrpc.server.html#module-xmlrpc.server
# https://docs.python.org/3/library/xml.etree.elementtree.html
# https://www.mediawiki.org/wiki/API:Opensearch
import datetime
import sys
from time import strftime
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import xml.etree.ElementTree as ET
from socketserver import ThreadingMixIn
import requests


tree = ET.parse("db.xml")
root = tree.getroot()


# https://docs.python.org/3/library/socketserver.html#socketserver.ThreadingMixIn
class ThreadedSimpleXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/t2",)


class RpcFunctions:
    def new_note(self, noteInput):
        append = False  # If True -> append to db, else create new entry

        # Check if note with same topic exists -> if yes, check if same note exists
        if(root.find(f"./topic/[@name='{noteInput['topic']}']")):
            append = True
            if(root.find(f"./topic/note/[@name='{noteInput['note']}']")):
                return "Note with that name already exists."

        parent = None
        if(append):
            parent = root.find(
                f"./topic/[@name='{noteInput['topic']}']")
        else:
            parent = ET.SubElement(
                root, "topic", {"name": noteInput['topic']})

        newNote = ET.SubElement(
            parent, "note", {"name": noteInput['note']})
        newText = ET.SubElement(newNote, "text")
        newText.text = noteInput['text']
        newDate = ET.SubElement(newNote, "timestamp")
        newDate.text = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S")

        updatedTree = ET.ElementTree(root)
        updatedTree.write("db.xml")
        return "Note added."

    def get_all_topics(self):
        all_topics_array = []
        for child in root:
            all_topics_array.append(
                {"tag": child.tag, "attribute": child.attrib})
        return all_topics_array

    def get_topic(self, topicName):
        all_notes_array = []
        for note in root.findall('topic'):
            if(note.attrib['name'] == topicName):
                for child in note:
                    all_notes_array.append(
                        {"tag": child.tag, "attribute": child.attrib})
        return all_notes_array

    # Return note content (text) and timestamp
    def get_note(self, noteName):
        note = root.find(f"./topic/note/[@name='{noteName}']")
        text = "".join(note.find("text").itertext())
        timestamp = "".join(note.find("timestamp").itertext())
        return {"note": noteName, "text": text, "timestamp": timestamp}

    # If topic is provided -> append results to existing topic
    def query_wikipedia(self, searchTerm, topic):
        session = requests.Session()
        URL = "https://en.wikipedia.org/w/api.php"
        response = session.get(url=URL, params={
                               "action": "opensearch", "namespace": "0", "limit": "1", "format": "json", "search": searchTerm})
        data = response.json()
        articleTitle = data[1][0]
        # articleDesc = data[2][0] Disabled on behalf of wikimedia
        articleUrl = data[3][0]

        if(not articleTitle or not articleUrl):
            return f"No results with search term {searchTerm}"

        if(topic):
            parent = root.find(f"./topic/[@name='{topic}']")
            if(not parent):
                return f"Topic '{topic}' not found."

            newNote = ET.SubElement(
                parent, "note", {"name": f"{articleTitle}-article"})
            newXMLText = ET.SubElement(newNote, "text")
            newXMLText.text = articleUrl
            newDate = ET.SubElement(newNote, "timestamp")
            newDate.text = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S")

            updatedTree = ET.ElementTree(root)
            updatedTree.write("db.xml")
            return f"Search results appended to '{topic}':\n\tTitle: {articleTitle}\n\tUrl: {articleUrl}"
        else:
            return f"Search results:\n\tTitle: {articleTitle}\n\tUrl: {articleUrl}"


def main():

    with ThreadedSimpleXMLRPCServer(("127.0.0.1", 8000), requestHandler=RequestHandler) as rpcserver:
        rpcserver.register_introspection_functions()

        rpcserver.register_instance(RpcFunctions())

        try:
            print("server running on '127.0.0.1:8000'")
            rpcserver.serve_forever()

        except KeyboardInterrupt:
            print("Shutting down...")
            sys.exit(0)


if __name__ == '__main__':
    main()
