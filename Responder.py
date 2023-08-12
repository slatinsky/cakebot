class Responder:
    def __init__(self, interaction):
        self.interaction = interaction
        self.msg_content = ""

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        pass

    async def send(self, message):
        self.msg_content = message + '\n'
        return await self.interaction.response.send_message(message)
    
    async def edit(self, message):
        self.msg_content = message + '\n'
        return await self.interaction.edit_original_response(content=message)
    
    async def append(self, message):
        self.msg_content += message + '\n'
        return await self.interaction.edit_original_response(content=self.msg_content)