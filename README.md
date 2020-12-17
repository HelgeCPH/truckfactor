# What is this?

This tool, `truckfactor` computes the 
[truck (bus/lorry/lottery) factor](https://en.wikipedia.org/wiki/Bus_factor) for a 
given Git repository.

The truck factor is

  > the number of people on your team that have to be hit by a truck (or quit) 
  > before the project is in serious trouble
  >
  > L. Williams and R. Kessler, Pair Programming Illuminated. Addison Wesley, 2003.

One of the earliest occurrences of the term in a real project was in the Python
mailing list: 
["If Guido was hit by a bus?"](https://legacy.python.org/search/hypermail/python-1994q2/1040.html)


## Installation

```
pip install truckfactor
```

### Requirements

The tool requires that `git` is installed and accessible on `PATH`.


## How to use it?

You have to either point the tool to a directory containing a Git repository or
to a URL with a remote repository. In case a URL is given, the tool will clone
the repository into a temporary directory.

From the terminal, the tool can be run as in the following:

```bash
$ truckfactor <path_or_url_to_repository>
The truck factor of <path_to_repository> is: <number>
```

For now, it just returns on line of text ending in the number of the truck 
factor for that repository.


Calling it from code:

```python
from truckfactor.compute import main


truckfactor = main("<path_to_repo>")
```


# How does the tool compute the truck factor?

In essence the tool does the following:

  * Reads a git log from the repository
  * Computes for each file who has the _knowledge ownership_ of it.
    - A contributor has knowledge ownership of a file when she edited the most 
    lines in it.
    - That computation is inspired by 
    [A. Thornhill _Your Code as a Crime Scene_](https://pragprog.com/titles/atcrime/your-code-as-a-crime-scene/).
    - Note, only for text files knowledge ownership is computed. The tool may 
    not, return a good answer for repositories containing only binary files.
  * Then similar to [G. Avelino et al. *A novel approach for estimating Truck Factors*](https://peerj.com/preprints/1233.pdf) 
  low-contributing authors are removed from the analysis as long as still more 
  than half of all files have a knowledge owner. The amount of remaining 
  knowledge owners is the truck factor of the given repository.
