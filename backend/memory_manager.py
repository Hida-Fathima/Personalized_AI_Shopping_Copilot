import re

class MemoryManager:
    def __init__(self):
        self.topic_memory = None      # main topic (e.g., "red dresses")
        self.last_messages = []       # last 5 messages only

    def add_message(self, text):
        # store only recent messages
        self.last_messages.append(text)
        if len(self.last_messages) > 5:
            self.last_messages.pop(0)

    def detect_new_topic(self, text):
        # Simple rule: shopping keywords → topic change
        shopping_keywords = [
            "dress", "shirt", "jeans", "shoes", "mobile", "earbuds",
            "tshirt", "kurti", "lehenga", "frock", "sandals"
        ]
        words = text.lower().split()

        return any(w in words for w in shopping_keywords)

    def update_topic(self, text):
        # if user message has a product category → it's a new topic
        if self.detect_new_topic(text):
            self.topic_memory = text
        # otherwise keep old topic

    def build_query_context(self, new_msg):
        """
        Combine topic + new message smartly.
        Example:
            topic="red dress"
            msg="under 500" → "red dress under 500"
        """
        if not self.topic_memory:
            return new_msg

        # user changed topic
        if self.detect_new_topic(new_msg):
            self.topic_memory = new_msg
            return new_msg

        # combine topic with the new request
        return f"{self.topic_memory} {new_msg}".strip()

memory = MemoryManager()
