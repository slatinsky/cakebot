from utils import Config

class Responder:
    def __init__(self, interaction):
        self.interaction = interaction
        self.header_rows = []
        self.rows = []
        self.msg_references = []
        self.msg_previous_content = []

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        pass

    async def disallow_execute_check(self):
        """
        raises an exception if the command should not be executed
        do not catch this exception if you want to stop the command from executing
        """
        deny_author_ids = []  # copy author id from discord

        if self.interaction.user.id in deny_author_ids:
            await self.interaction.response.send_message("You are not allowed to use this bot.", ephemeral=True)
            raise Exception("User not allowed to use bot.")  # do not allow commands from these users

        if self.interaction.channel_id not in Config.ALLOWED_CHANNEL_IDS:
            await self.interaction.response.send_message("This channel is not allowed for this bot.", ephemeral=True)
            raise Exception("Wrong channel ID.")  # not correct channel ID, ignore command

        if self.interaction.guild is None:
            await self.interaction.send("Don't be shy! Talk with me in bot-channel!")
            raise Exception("Wrong channel ID - dm.")  # not correct channel ID, ignore command


    async def split(self, rows: list[str]) -> list[str]:
        """
        Splits the message into multiple messages, each with a maximum of 2000 characters.
        keeps code blocks formatted between messages.
        """
        messages = []
        current_message = ""
        char_limit = 2000
        code_block = ""
        for row in rows:
            if row.startswith("```"):
                if code_block == "":
                    code_block = row
                else:
                    code_block = ""
            if len(current_message) + len(row) + 2*len(code_block) > char_limit:
                # add ending code block
                if code_block != "":
                    current_message += "```\n"

                messages.append(current_message[:-1])
                current_message = ""

                # add starting code block
                if code_block is not None:
                    current_message = code_block + "\n"
                

            current_message += row + "\n"

        messages.append(current_message[:-1])

        # for message in messages:
        #     print(message)
        #     print("-----", len(message))
        return messages
    
    async def render(self, rows):
        """
        compares the new messages with the previously messages and edits the changed ones
        deletes excess messages
        """
        split_messages = await self.split(rows)

        # print(split_messages, flush=True)

        # send messages or edit them if they changed
        for i, message in enumerate(split_messages):

            print(i, len(message), message, flush=True)
            if i == 0:
                # interaction response
                if len(self.msg_previous_content) > 0:
                    # edit existing
                    if message != self.msg_previous_content[i]:
                        await self.interaction.edit_original_response(content=message)
                        self.msg_previous_content[0] = message
                    else:
                        print("no change", i, flush=True)

                else:
                    # create new
                    await self.interaction.response.send_message(message)
                    self.msg_previous_content.append(message)


            else:
                # channel msg
                if len(self.msg_references) > i - 1:
                    # edit existing
                    if message != self.msg_previous_content[i]:
                        await self.msg_references[i-1].edit(content=message)   # i-1 because the first message is the interaction response, not channel msg
                        self.msg_previous_content[i-1] = message
                    else:
                        print("no change.", i, flush=True)
                else:
                    # create new
                    self.msg_references.append(await self.interaction.channel.send(message))
                    self.msg_previous_content.append(message)
                
        # delete excess messages
        for i in range(len(split_messages), len(self.msg_references) + 1):
            await self.msg_references[i-1].delete()
            del self.msg_references[i-1]
            del self.msg_previous_content[i-1]
        
    async def append(self, message: str):
        """
        appends a message to the end of the current message
        """
        self.rows += message.split('\n')
        await self.render(self.header_rows + self.rows)

    async def append_header(self, message: str):
        """
        appends a message to the end of the current header message
        useful for temporary logs
        """
        self.header_rows += message.split('\n')
        await self.render(self.header_rows + self.rows)

    async def replace_header(self, message: str):
        """
        replaces the current header message
        useful for clearing temporary logs after they are no longer needed
        """
        self.header_rows = [message]
        await self.render(self.header_rows + self.rows)