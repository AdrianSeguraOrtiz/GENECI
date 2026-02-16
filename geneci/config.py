import random
import string

__version__ = "5.0.0"
__author__ = "Adrian Segura Ortiz <adrianseor.99@uma.es>"

HEADER = "\n".join(
    [
        f"[bold cyan]GENECI[/bold cyan] [dim]v{__version__}[/dim]",
        "[dim]Gene Network Consensus Inference[/dim]",
        "[dim]Use `geneci --help` to list commands[/dim]",
    ]
)

# Generate temp folder name
temp_folder_str = "tmp-" + "".join(random.choices(string.ascii_lowercase, k=10))

# Docker tag
tag = "5.0.0"
