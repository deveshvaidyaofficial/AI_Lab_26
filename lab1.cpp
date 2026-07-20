#include <iostream>
using namespace std;

struct Node
{
    int vertex;
    Node *next;
};

Node *adj[100];
int visited[100];

int *Q;
int front = -1, rear = -1, maxSize;

//---------------------- Queue Functions ----------------------//

void createQueue(int size)
{
    maxSize = size;
    Q = new int[maxSize];
    front = rear = -1;
}

bool isEmpty()
{
    return (front == -1 || front > rear);
}

bool isFull()
{
    return (rear == maxSize - 1);
}

void enqueue(int value)
{
    if (isFull())
    {
        cout << "Queue Overflow\n";
        return;
    }

    if (front == -1)
        front = 0;

    Q[++rear] = value;
}

int dequeue()
{
    if (isEmpty())
        return -1;

    return Q[front++];
}

//---------------------- Graph Functions ----------------------//

bool edgeExists(int u, int v)
{
    Node *temp = adj[u];

    while (temp != NULL)
    {
        if (temp->vertex == v)
            return true;

        temp = temp->next;
    }

    return false;
}

void addEdge(int u, int v)
{
    Node *newNode = new Node;
    newNode->vertex = v;
    newNode->next = adj[u];
    adj[u] = newNode;

    newNode = new Node;
    newNode->vertex = u;
    newNode->next = adj[v];
    adj[v] = newNode;
}

//---------------------- BFS ----------------------//

void BFS(int v)
{
    int u = v;
    visited[v] = 1;

    front = rear = -1;

    while (true)
    {
        cout << u << " ";

        Node *temp = adj[u];

        while (temp != NULL)
        {
            int w = temp->vertex;

            if (visited[w] == 0)
            {
                enqueue(w);
                visited[w] = 1;
            }

            temp = temp->next;
        }

        if (isEmpty())
            return;

        u = dequeue();
    }
}

void BFT(int source, int n)
{
    for (int i = 0; i < n; i++)
        visited[i] = 0;

    BFS(source);

    for (int i = 0; i < n; i++)
    {
        if (visited[i] == 0)
            BFS(i);
    }
}

//---------------------- DFS ----------------------//

void DFS(int v)
{
    visited[v] = 1;

    cout << v << " ";

    Node *temp = adj[v];

    while (temp != NULL)
    {
        if (visited[temp->vertex] == 0)
            DFS(temp->vertex);

        temp = temp->next;
    }
}

void DFT(int source, int n)
{
    for (int i = 0; i < n; i++)
        visited[i] = 0;

    DFS(source);

    for (int i = 0; i < n; i++)
    {
        if (visited[i] == 0)
            DFS(i);
    }
}

//---------------------- Main ----------------------//

int main()
{
    int n, e;

    cout << "Enter number of vertices: ";
    cin >> n;

    createQueue(n);

    for (int i = 0; i < n; i++)
        adj[i] = NULL;

    int maxEdges = (n * (n - 1)) / 2;

    do
    {
        cout << "Enter number of edges (Maximum " << maxEdges << "): ";
        cin >> e;

        if (e < 0 || e > maxEdges)
            cout << "Invalid number of edges! Please enter again.\n";

    } while (e < 0 || e > maxEdges);

    cout << "Enter the edges (u v):\n";

    for (int i = 0; i < e;)
    {
        int u, v;
        cin >> u >> v;

        if (u < 0 || u >= n || v < 0 || v >= n)
        {
            cout << "Invalid vertex! Enter the edge again.\n";
            continue;
        }

        if (u == v)
        {
            cout << "Self-loops are not allowed. Enter the edge again.\n";
            continue;
        }

        if (edgeExists(u, v))
        {
            cout << "Duplicate edge! Enter a different edge.\n";
            continue;
        }

        addEdge(u, v);
        i++;
    }

    int choice;

    do
    {
        cout << "\n========== GRAPH MENU ==========\n";
        cout << "1. Breadth First Traversal (BFS)\n";
        cout << "2. Depth First Traversal (DFS)\n";
        cout << "3. Exit\n";
        cout << "Enter your choice: ";
        cin >> choice;

        switch (choice)
        {
        case 1:
        {
            int source;

            cout << "Enter source vertex: ";
            cin >> source;

            if (source < 0 || source >= n)
            {
                cout << "Invalid source vertex!\n";
                break;
            }

            cout << "\nBreadth First Traversal:\n";
            BFT(source, n);
            cout << endl;

            break;
        }

        case 2:
        {
            int source;

            cout << "Enter source vertex: ";
            cin >> source;

            if (source < 0 || source >= n)
            {
                cout << "Invalid source vertex!\n";
                break;
            }

            cout << "\nDepth First Traversal:\n";
            DFT(source, n);
            cout << endl;

            break;
        }

        case 3:
            cout << "Exiting...\n";
            break;

        default:
            cout << "Invalid choice!\n";
        }

    } while (choice != 3);

    delete[] Q;

    return 0;
}