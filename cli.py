from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from enum import Enum
from client import MCPClient


class CommandType(Enum):
    QUERY = "query"
    DEBUG = "debug"
    REFRESH = "refresh"
    TOOLS = "tools"
    RESOURCES = "resources"
    RESOURCE = "resource"
    QUIT = "quit"

class MCPClientCLI:
    def __init__(self, client: MCPClient):
        self.client = client
        self.console = Console()

    def parse_command(self, input_text: str) -> tuple[CommandType, str]:
        """Parse input to determine command type and payload"""
        input_text = input_text.strip().lower()
        
        if input_text == 'quit':
            return CommandType.QUIT, ""
        elif input_text == '/debug':
            return CommandType.DEBUG, ""
        elif input_text == '/refresh':
            return CommandType.REFRESH, ""
        elif input_text == '/tools':
            return CommandType.TOOLS, ""
        elif input_text == '/resources':
            return CommandType.RESOURCES, ""
        elif input_text.startswith('/resource:'):
            return CommandType.RESOURCE, input_text[10:].strip()
        else:
            return CommandType.QUERY, input_text

    async def handle_debug_command(self):
        """Handle debug toggle command"""
        self.client.debug = not self.client.debug
        self.console.print(
            f"[{'green' if self.client.debug else 'red'}]Debug mode "
            f"{'enabled' if self.client.debug else 'disabled'}[/]"
        )

    async def handle_refresh_command(self):
        """Handle refresh capabilities command"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            progress.add_task("Refreshing capabilities...", total=None)
            await self.client.refresh_capabilities()
        self.console.print("[green]Capabilities refreshed successfully[/]")

    async def handle_tools_command(self):
        """Handle tools listing command"""
        tools = await self.client.list_tools()
        tools_table = Table(title="Available Tools", box=box.ROUNDED)
        tools_table.add_column("Tool", style="cyan", no_wrap=False)
        tools_table.add_column("Description", style="green", no_wrap=False)
        
        for tool in tools:
            tools_table.add_row(
                tool.name,
                tool.description or "No description available"
            )
        self.console.print(tools_table)

    async def handle_resources_command(self):
        """Handle resources listing command"""
        resources = await self.client.list_resources()
        resources_table = Table(title="Available Resources", box=box.ROUNDED)
        resources_table.add_column("URI", style="cyan", no_wrap=False)
        resources_table.add_column("Name", style="blue")
        resources_table.add_column("Description", style="green", no_wrap=False)
        
        for resource in resources:
            resources_table.add_row(
                str(resource.uri),
                resource.name,
                resource.description or "No description available"
            )
        self.console.print(resources_table)

    async def handle_resource_command(self, uri: str):
        """Handle resource reading command"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            progress.add_task("Loading resource...", total=None)
            content = await self.client.read_resource(uri)
        
        if content.startswith("```") or content.startswith("#"):
            self.console.print(Markdown(content))
        else:
            self.console.print(Panel(content, title=uri, border_style="blue"))

    async def handle_query(self, query: str):
        """Handle general query processing"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            progress.add_task("Processing query...", total=None)
            response = await self.client.process_query(query)
        
        if "```" in response or "#" in response:
            self.console.print(Markdown(response))
        else:
            self.console.print(Panel(response, border_style="green"))

    async def chat_loop(self):
        """Run an interactive chat loop with rich UI"""
        self.print_welcome_header()

        # Command handlers mapping
        handlers = {
            CommandType.DEBUG: self.handle_debug_command,
            CommandType.REFRESH: self.handle_refresh_command,
            CommandType.TOOLS: self.handle_tools_command,
            CommandType.RESOURCES: self.handle_resources_command,
            CommandType.RESOURCE: self.handle_resource_command,
            CommandType.QUERY: self.handle_query
        }

        while True:
            try:
                query = Prompt.ask("\n[bold blue]Query[/]").strip()
                command_type, payload = self.parse_command(query)

                if command_type == CommandType.QUIT:
                    break

                handler = handlers.get(command_type)
                if handler:
                    if payload:
                        await handler(payload)
                    else:
                        await handler()
            except KeyboardInterrupt:
                self.console.print("[yellow]Shutting down client...[/]", style="yellow")
                break
            except Exception as e:
                self.console.print(f"[red]Error:[/] {str(e)}", style="bold red")

        # Shutdown message
        self.console.print(Panel(
            "[yellow]Shutting down client...[/]",
            border_style="yellow",
            box=box.DOUBLE
        ))

    def print_welcome_header(self):
        ascii_art = """[bold blue]
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║  ███╗   ███╗ ██████╗██████╗     ██████╗ ███╗   ███╗███╗   ██╗██╗       ║
    ║  ████╗ ████║██╔════╝██╔══██╗   ██╔═══██╗████╗ ████║████╗  ██║██║       ║
    ║  ██╔████╔██║██║     ██████╔╝   ██║   ██║██╔████╔██║██╔██╗ ██║██║       ║
    ║  ██║╚██╔╝██║██║     ██╔═══╝    ██║   ██║██║╚██╔╝██║██║╚██╗██║██║       ║
    ║  ██║ ╚═╝ ██║╚██████╗██║        ╚██████╔╝██║ ╚═╝ ██║██║ ╚████║██║       ║
    ║  ╚═╝     ╚═╝ ╚═════╝╚═╝         ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝       ║
    ║                                                                           ║
    ║     [cyan]Model[/] · [cyan]Context[/] · [cyan]Protocol[/]  →  [green]OMNI CONNECT[/]              ║
    ╚═══════════════════════════════════════════════════════════════════════════╝[/]
    """
        
        # Server status with emojis and cool styling
        server_status = [f"[bold green]●[/] [cyan]{name}[/]" for name in self.client.server_names]
        
        content = f"""
{ascii_art}

[bold magenta]🚀 Universal MCP Client[/]

[bold white]Connected Servers:[/]
{' | '.join(server_status)}

[dim]▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰[/]
[cyan]Your Universal Gateway to MCP Servers[/]
[dim]▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰[/]
"""
        
        # Add some flair with a fancy border
        self.console.print(Panel(
            content,
            title="[bold blue]⚡ MCPOmni Connect ⚡[/]",
            subtitle="[bold cyan]v0.0.1[/]",
            border_style="blue",
            box=box.DOUBLE_EDGE
        ))

        # Command list with emojis and better styling
        commands_table = Table(
            title="[bold magenta]Available Commands[/]",
            box=box.SIMPLE_HEAD,
            border_style="bright_blue"
        )
        commands_table.add_column("[bold cyan]Command[/]", style="cyan")
        commands_table.add_column("[bold green]Description[/]", style="green")
        
        commands = [
            ("/debug", "Toggle debug mode 🐛"),
            ("/refresh", "Refresh server capabilities 🔄"),
            ("/tools", "List available tools ��️"),
            ("/resources", "List available resources 📚"),
            ("/resource:<uri>", "Read a specific resource 🔍"),
            ("quit", "Exit the application 👋")
        ]
        
        for cmd, desc in commands:
            commands_table.add_row(cmd, desc)
        
        self.console.print(commands_table)


