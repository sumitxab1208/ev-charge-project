#include <iostream>
using namespace std;

#define SIZE 10

class HashTable {
    int table[SIZE];

public:
    HashTable() {
        for(int i = 0; i < SIZE; i++) {
            table[i] = -1;   // -1 means empty
        }
    }

    // Hash function
    int hashFunction(int key) {
        return key % SIZE;
    }

    // Linear Probing Insert
    void insertLinear(int key) {
        int index = hashFunction(key);
        int original = index;

        while(table[index] != -1) {
            cout << "Collision at index " << index << " for key " << key << endl;
            index = (index + 1) % SIZE;

            if(index == original) {
                cout << "Hash table is full\n";
                return;
            }
        }

        table[index] = key;
        cout << "Inserted " << key << " at index " << index << endl;
    }

    // Quadratic Probing Insert
    void insertQuadratic(int key) {
        int index = hashFunction(key);
        int i = 1;

        while(table[index] != -1) {
            cout << "Collision at index " << index << " for key " << key << endl;
            index = (hashFunction(key) + i*i) % SIZE;
            i++;

            if(i == SIZE) {
                cout << "Hash table is full\n";
                return;
            }
        }

        table[index] = key;
        cout << "Inserted " << key << " at index " << index << endl;
    }

    // Search function
    void search(int key) {
        int index = hashFunction(key);
        int i = 0;

        while(table[(index + i) % SIZE] != -1 && i < SIZE) {
            if(table[(index + i) % SIZE] == key) {
                cout << "Key " << key << " found at index " << (index + i) % SIZE << endl;
                return;
            }
            i++;
        }

        cout << "Key " << key << " not found\n";
    }

    // Display table
    void display() {
        cout << "\nHash Table:\n";
        for(int i = 0; i < SIZE; i++) {
            cout << i << " -> ";
            if(table[i] != -1)
                cout << table[i];
            else
                cout << "Empty";
            cout << endl;
        }
    }
};

int main() {
    HashTable h;

    // Insert elements (will cause collisions)
    cout << "Linear Probing:\n";
    h.insertLinear(10);
    h.insertLinear(20);
    h.insertLinear(30);
    h.insertLinear(25);  // collision example
    h.insertLinear(35);  // collision example

    h.display();

    // Search
    h.search(25);
    h.search(99);

    return 0;
}