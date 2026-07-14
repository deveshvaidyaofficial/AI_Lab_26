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

void BFT(int n)
{
    for (int i = 0; i < n; i++)
        visited[i] = 0;

    for (int i = 0; i < n; i++)
    {
        if (visited[i] == 0)
            BFS(i);
    }
}

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

    cout << "\nBreadth First Traversal:\n";
    BFT(n);

    delete[] Q;

    return 0;
}