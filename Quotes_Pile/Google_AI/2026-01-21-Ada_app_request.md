Prompt:

Create me an Ada app that turns a Git project directory into a markdown and Wiki host. Ubuntu Linux, but try to make standard Ada-compliant code (latest standard)

wiki_host.gpr 

with "aws";
with "ada_wiki";

project Wiki_Host is
   for Main use ("main.adb");
   for Source_Dirs use ("src");
   for Object_Dir use "obj";
end Wiki_Host;


src/main.adb

with AWS.Default;
with AWS.Server;
with AWS.Response;
with AWS.Status;
with Wiki.Parsers.Markdown;
with Wiki.Renderers.Html;
with Ada.Text_IO;
with Ada.Directories;
with Ada.Strings.Unbounded;

procedure Main is
   use Ada.Strings.Unbounded;
   
   Server_Port : constant Positive := 8080;
   Git_Repo_Path : constant String := "/path/to/your/git/repo"; -- Path to .md files

   -- Callback to handle incoming HTTP requests
   function Wiki_Handler (Request : AWS.Status.Data) return AWS.Response.Data is
      URI      : constant String := AWS.Status.URI (Request);
      Filename : constant String := Git_Repo_Path & URI;
      Content  : Unbounded_String;
   begin
      -- Basic Routing: Look for .md files matching the URL
      if Ada.Directories.Exists (Filename & ".md") then
         declare
            Parser   : Wiki.Parsers.Markdown.Markdown_Parser;
            Renderer : Wiki.Renderers.Html.Html_Renderer;
            Doc      : Wiki.Nodes.Wiki_Document;
         begin
            -- 1. Parse Markdown file
            Parser.Parse (Filename & ".md", Doc);
            -- 2. Render to HTML
            Renderer.Render (Doc, Content);
            
            return AWS.Response.Build ("text/html", To_String (Content));
         end;
      else
         return AWS.Response.Build ("text/plain", "404 - Wiki page not found", 
                                    AWS.Messages.S404);
      end if;
   end Wiki_Handler;

   WS : AWS.Server.HTTP;
begin
   Ada.Text_IO.Put_Line ("Starting Wiki Host on port" & Server_Port'Image);
   AWS.Server.Start (WS, "WikiHost", 
                     Callback => Wiki_Handler'Access,
                     Port     => Server_Port);
   
   -- Keep server alive
   AWS.Server.Wait (AWS.Server.Q_Key_Pressed);
   AWS.Server.Stop (WS);
end Main;

