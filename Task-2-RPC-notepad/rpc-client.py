# https://docs.python.org/3/library/xmlrpc.client.html#module-xmlrpc.client
import xmlrpc.client


rpcServer = xmlrpc.client.ServerProxy("http://127.0.0.1:8000/t2")


def new_note():
    topic = input("Note topic: ")
    name = input("Note name: ")
    text = input("Text content: ")
    if(not topic or not name or not text):
        print("Topic, name and text must be submitted.")
        return
    newNote = {"topic": topic, "note": name, "text": text}
    try:
        print(rpcServer.new_note(newNote))

    except xmlrpc.client.Fault as e:
        print("Error occurred, please try again.", e)


def get_note():
    try:
        topics = rpcServer.get_all_topics()
        print("Available topics:")

        for topic in topics:
            print(f"\t{topic['attribute']['name']}")
        topic = input("\nSelect a topic to retrieve the note from: ")

        # First query the desired topic and print all possible notes
        notes_array = rpcServer.get_topic(topic)
        print("Available notes:")
        for note in notes_array:
            print(f"\t{note['attribute']['name']}")

        noteName = input("Select a note to retrieve: ")

        # Then find the note and print content
        note = rpcServer.get_note(noteName)
        print(
            f"\n{note['note']}:\n\ttime: {note['timestamp']}\n\ttext: {note['text']}")

    except xmlrpc.client.Fault as e:
        print("Error occurred, please try again.")


def query_wikipedia():
    try:
        searchTerm = input("Enter search term: ")
        if(not searchTerm):
            print("Search term must be submitted")
            return

        print("To which topic would you like to append the results?",
              "\n(Leave blank if you don't want to append the results)")
        topic = input("Topic: ")
        res = rpcServer.query_wikipedia(searchTerm, topic)
        print(res)
    except xmlrpc.client.Fault as e:
        print("Error occured, please try again.")


def main():
    print("------------------------------",
          "\n|      XML-RPC Notebook      |",
          "\n------------------------------")

    while(True):
        print('''\nOptions:
    1) Add a new note
    2) Get a note from a topic
    3) Query wikipedia
    0) Exit
        ''')
        choice = input("Enter your choice: ")

        if(choice == "0"):
            break
        elif(choice == "1"):
            new_note()

        elif(choice == "2"):
            get_note()

        elif(choice == "3"):
            query_wikipedia()
        else:
            print("Invalid choice, try again.")


if __name__ == '__main__':
    main()
