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
        self.rows += message.split('\n')
        await self.render(self.header_rows + self.rows)

    async def append_header(self, message: str):
        self.header_rows += message.split('\n')
        await self.render(self.header_rows + self.rows)

    async def replace_header(self, message: str):
        self.header_rows = [message]
        await self.render(self.header_rows + self.rows)
            
        # self.msg_content += message + '\n'
        # return await self.interaction.edit_original_response(content=self.msg_content)