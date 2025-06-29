from vectordb import Memory
import pprint
from logic.iching import get_hexagram_section

memory = Memory(memory_file='fl.pkl', chunking_strategy={'mode':'sliding_window', 'window_size': 128, 'overlap': 16})

if len(memory.memory) < 10:
    for i in range(1, 65):
        hexagram = get_hexagram_section(i)
        memory.save(hexagram.Content, hexagram)

def search(query):
    results = memory.search(query, top_n=5)
    return results

if __name__ == '__main__':
    search('What is the meaning of the hexagram 1?')
