from bs4 import BeautifulSoup
import requests
import csv
import os
import nltk
import pandas as pd
import json
nltk.download('stopwords')
from nltk.corpus import stopwords
import pyTigerGraph as tg

def get_packages(link):
    '''
    Input: Link of the endpoint -> link
    
    This link is used to receive the HTML response and BeautifulSoup is used to scrape the data about names of packages from the response.

    Return: List of package received from the HTML response
    '''
    packages = []
    # Creating a BeautifulSoup
    soup = BeautifulSoup(requests.get(link).content,'html.parser')
    # Finding the specific class of object in which we have package name
    html_data = soup.find_all('a',class_="package-snippet")
    # Adding the name of packages to the list
    for package in html_data:
        packages.append(str(package).split('/')[2])
    return packages



def fetch_data(response):
    '''
    Input: Json of package meta data -> response

    This function takes the data in json and add the nesseary things of the data in a list 

    Return: List of data containing package name,author,email,license,development status,programming language and dependency
    '''
    package_name = response['info']['name'] 
    package_author = response['info']['author'] if response['info']['author'] != None else ''
    package_author_email = response['info']['author_email'] if response['info']['author_email'] != None else ''
    package_license = response['info']['license'] if response['info']['license'] != None else ''
    programming_lang = set()
    package_dev_status = ''
    classifier = response["info"]['classifiers'] if response["info"]['classifiers'] != None else []
    for classifier in response["info"]['classifiers']:
        classifier_list = classifier.split(' :: ')
        if 'Development Status' in classifier_list:
            package_dev_status = classifier_list[-1]
        elif 'Programming Language' in classifier_list:
            programming_lang.add(classifier_list[1])
    package_dependency = set()
    requires_dist = response["info"]['requires_dist'] if response["info"]['requires_dist'] != None else []
    for dependency in requires_dist:
        package_dependency.add(dependency.split()[0])
    
    return [package_name,package_author,package_author_email,package_license,package_dev_status,programming_lang,package_dependency]



def create_directory(Search_Context):
    '''
    Input: Space seperaetd keywords to be searched -> Search_Context (In address or any operation _ is used to join the Search_Context)

    This function creates the folder in ../library named as {Search_Context}

    Then, creates 3 csv(s) in the folder adding the name of attributes/columns in each csv
    '''
    directory = '_'.join(Search_Context.split())
    # Parent Directory path
    parent_dir = "C:/Users/anime/Documents/PypiReCom/Code/library/"
    # Defining the path as ../library/{directory}
    path = os.path.join(parent_dir, directory)
    # Creating the directory
    os.mkdir(path)

    # Creating the differnt csv(s)
    base_directory = "library/"+'_'.join(Search_Context.split())
    try:
        with open(base_directory+"/Package_Basic_Data.csv","a", newline='') as file:
            csv_file = csv.writer(file)
            csv_file.writerow(['package_name','package_author','package_author_email','package_license','package_dev_status','search_meta'])
        with open(base_directory+"/Package_Dependency.csv","a", newline='') as file:
            csv_file = csv.writer(file)
            csv_file.writerow(['package_name','dependency_pkg'])
        with open(base_directory+"/Package_Prog_Lang.csv","a", newline='') as file:
            csv_file = csv.writer(file)
            csv_file.writerow(['package_name','language'])
    except:
        print('Error in creating file')



def save_data(Search_Context,data):
    '''
    Input: Space seperaetd keywords to be searched -> Search_Context (In address or any operation _ is used to join the Search_Context), 
           List of data containing package name,author,email,license,development status,programming language and dependency -> data
    
    This function loads data in 3 csv(s) in the ../library/{Search_Context} and inserts the nessesary data in each csv.
    '''
    # Inserting Data into Different files
    base_directory = "library/"+'_'.join(Search_Context.split())
    try:
        # Saving data to files
        package_name,package_author,package_author_email,package_license,package_dev_status,programming_lang,package_dependency = data
        with open(base_directory+"/Package_Basic_Data.csv","a", newline='') as file:
            csv_file = csv.writer(file)
            csv_file.writerow([package_name,package_author,package_author_email,package_license,package_dev_status,''])
        with open(base_directory+"/Package_Dependency.csv","a", newline='') as file:
            csv_file = csv.writer(file)
            for dependency_pkg in package_dependency:
                csv_file.writerow([package_name,dependency_pkg])
        with open(base_directory+"/Package_Prog_Lang.csv","a", newline='') as file:
            csv_file = csv.writer(file)
            for language in programming_lang:
                csv_file.writerow([package_name,language])
    except:
        print('Error in saving')



def generate_context(search_text):
    '''
    This function generates the search context by taking the text being searched as input and returns the text after removing the stop words.

    Input: The text being searched -> Search_Text (In address or any operation _ is used to join the Search_Context)

    Return: Text without stopwords -> Search_Context 
    '''
    # Removing stop words
    stop_words = stopwords.words('english')
    words = search_text.split()
    Search_Context = []
    for word in words:
        if word not in stop_words:
            Search_Context.append(word)
    return ' '.join(Search_Context)



def fetch_and_update_graph(Search_Context):
    '''
    Input parameter: Space seperaetd keywords to be searched -> Search_Context (In address or any operation _ is used to join the Search_Context)

    This function scrapes data from the pypi website after searching the Search_Context
    
    Create a new folder/directory under library in the name of Search_Context
    
    Creates 3 different csv(s) of the packages meta data
    
    Generates the graph of the Search_Context
    '''
    with open("library/index.csv","a",newline='') as file:
        csv_file = csv.writer(file)
        csv_file.writerow(['_'.join(Search_Context.split())])
        
    # Data scrapping required for getting list of packages
    packages = []
    # Taking 100 Packages from the first 5 pages
    for page in range(1,6):
        packages += get_packages('https://pypi.org/search/?q=' + '+'.join(Search_Context.split()) + '&page=' + str(page))

    # creating directory
    create_directory(Search_Context)
    
    # Getting data of each package in the package list
    for package in packages:
        # Package data in Json format
        try:
            response = (requests.get('https://pypi.python.org/pypi/'+package+'/json')).json()
            # Picking nesseary data form Json file
            data = fetch_data(response)
            # Saving data in library
            save_data(Search_Context,data)
        except:
            print("Error in response")
    
    # Graph Generation function
    generate_graph(Search_Context)



def generate_graph(Search_Context):     
    '''
    Generating the graph by extracting the data from the csv(s) generated and updating on Tiger Graoh
    
    Input: Space seperaetd keywords to be searched -> Search_Context (In address or any operation _ is used to join the Search_Context)

    Output: Json response of graph query.
    ''' 
    base_directory = "library/"+'_'.join(Search_Context.split())

    try:
        # making connection
        conn = tg.TigerGraphConnection(
            host='https://cab6c8c57c1140ac9283258d135b57d6.i.tgcloud.io',
            graphname='Test',
            gsqlSecret='elgabddfotvdu68tgmq0b79d6a1pqevh',
        )
        auth_token = conn.getToken('elgabddfotvdu68tgmq0b79d6a1pqevh')
        # Deleting the current graph data
        conn.delVertices("Package")
        conn.delVertices("Programming_Lang")
        conn.delVertices("License")
        conn.delVertices("Dependency_Package")
        conn.delVertices("Dev_Status")

        # Creating list for bulk updatation
        package_vertex, edge_1, edge_2, edge_3, edge_4 = []

        # Extracting data from Package_Basic_Data csv
        data = []
        with open(base_directory+"/Package_Basic_Data.csv","r") as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                data.append(row)
        df = pd.DataFrame(data) # Creating Dataframe
        df.columns = df.iloc[0] #Setting columns as 1dt row
        df = df.tail(-1)    #Removing 1st row
        # Adding data tupple in list for updation
        for index in df.index:
            package_vertex.append((df["package_name"][index], {"author" : df["package_author"][index],
                                                                "author_email" : df["package_author_email"][index],
                                                                "dev_status" : df["package_dev_status"][index],
                                                                "search_meta" : df["search_meta"][index]}))
            edge_1.append((df["package_name"][index],df["package_dev_status"][index],{}))
            edge_2.append((df["package_name"][index],df["package_license"][index],{}))

        # Extracting data from Package_Prog_Lang csv
        data = []
        with open(base_directory+"/Package_Prog_Lang.csv","r") as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                data.append(row)
        df = pd.DataFrame(data) # Creating Dataframe
        df.columns = df.iloc[0] #Setting columns as 1dt row
        df = df.tail(-1)    #Removing 1st row
        # Adding data tupple in list for updation
        for index in df.index:
            edge_3.append((df["package_name"][index],df["language"][index],{}))
        
        # Extracting data from Package_Dependency csv
        data = []
        with open(base_directory+"/Package_Dependency.csv","r") as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                data.append(row)
        df = pd.DataFrame(data) # Creating Dataframe
        df.columns = df.iloc[0] #Setting columns as 1dt row
        df = df.tail(-1)    #Removing 1st row
        # Adding data tupple in list for updation
        for index in df.index:
            edge_4.append((df["package_name"][index],df["dependency_pkg"][index],{}))

        result = (conn.upsertVertices("Package",package_vertex) and conn.upsertEdges("Package","curr_status","Dev_Status",edge_1)
                and conn.upsertEdges("Package","has_license","License",edge_2) and conn.upsertEdges("Package","used_language","Programming_Lang",edge_3)
                and conn.upsertEdges("Package","has_dependency","Dependency_Package",edge_4))
        if result:
            print("Graph Generated for "+Search_Context)
            graph = conn.runInstalledQuery("Stable_packages")
            with open(base_directory+"/graph.json", "w") as graphfile:
                json.dump(graph[0], graphfile)
        else:
            print("Error in graph generation.")
    except:
        print("Connection error")



def graph(Search_Context):
    '''
    Input: Space seperated text to be searched -> Search_Context (In address or any operation _ is used to join the Search_Context)

    Function checks for the graph file in ../library/{Seach_Context}

    Output: Returns the graph data in json format.
    '''
    # Creating the base address
    base_directory = "library/"+'_'.join(Search_Context.split())
    # Seaching for the graph in the base address
    with open(base_directory+"/graph.json", "r") as graphfile:
        return json.load(graphfile) 

    # elgabddfotvdu68tgmq0b79d6a1pqevh