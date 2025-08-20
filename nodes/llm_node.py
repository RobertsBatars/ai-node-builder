# nodes/llm_node.py
import json
import base64
import copy
from typing import Dict, List, Any, Optional, Tuple
from core.definitions import BaseNode, SocketType, InputWidget, MessageType, SKIP_OUTPUT, NodeStateUpdate

try:
    import litellm
except ImportError:
    litellm = None

class LLMNode(BaseNode):
    """
    A node that provides access to any LLM via the litellm library.
    Supports tool calling, context integration, and multimodal inputs.
    """
    CATEGORY = "AI"
    
    INPUT_SOCKETS = {
        "prompt": {"type": SocketType.TEXT, "is_dependency": True},
        "system_prompt": {"type": SocketType.TEXT, "is_dependency": True},
        "image": {"type": SocketType.TEXT, "is_dependency": True},
        "tools": {"type": SocketType.ANY, "array": True, "is_dependency": True}
    }
    
    OUTPUT_SOCKETS = {
        "response": {"type": SocketType.TEXT},
        "tool_calls": {"type": SocketType.ANY, "array": True}
    }
    
    # Model and provider configuration
    provider = InputWidget(widget_type="TEXT", default="openai")
    
    model = InputWidget(widget_type="TEXT", default="gpt-4o")
    
    api_key = InputWidget(widget_type="TEXT", default="")
    
    # LLM parameters
    temperature = InputWidget(widget_type="SLIDER", default=0.7,
                             properties={"min": 0.0, "max": 2.0, "step": 0.1})
    
    max_tokens = InputWidget(widget_type="NUMBER", default=1000,
                            properties={"min": 1, "max": 8000})
    
    top_p = InputWidget(widget_type="SLIDER", default=1.0,
                       properties={"min": 0.0, "max": 1.0, "step": 0.1})
    
    # Context control
    use_display_context = InputWidget(widget_type="BOOLEAN", default=False)
    
    display_context_filter = InputWidget(widget_type="COMBO", default="user_and_self",
                                        properties={"values": ["all", "user_and_self"]})
    
    use_runtime_memory = InputWidget(widget_type="BOOLEAN", default=True)
    
    enable_tools = InputWidget(widget_type="BOOLEAN", default=True)
    
    output_intermediate_messages = InputWidget(widget_type="BOOLEAN", default=False)

    def load(self):
        """Initialize the LLM node."""
        if litellm is None:
            raise ImportError("litellm library is required. Install with: pip install litellm")
        
        # Initialize conversation history and tool definitions in memory
        if 'conversation_history' not in self.memory:
            self.memory['conversation_history'] = []
        if 'tool_definitions' not in self.memory:
            self.memory['tool_definitions'] = []
        if 'pending_tool_calls' not in self.memory:
            self.memory['pending_tool_calls'] = None
        if 'current_execution_messages' not in self.memory:
            self.memory['current_execution_messages'] = []
        if 'processed_tool_results' not in self.memory:
            self.memory['processed_tool_results'] = {}
        if 'base_messages_built' not in self.memory:
            self.memory['base_messages_built'] = False  # Track if we've built the base message array
        if 'base_messages' not in self.memory:
            self.memory['base_messages'] = []  # Store the base conversation messages

    async def execute(self, prompt=None, system_prompt=None, image=None, tools=None):
        """Execute the LLM call with context integration and tool support."""
        try:
            # Check if we received tool results (tools parameter contains results instead of definitions)
            tool_results = None
            if tools and isinstance(tools, list) and len(tools) > 0:
                # Separate tool results from tool definitions
                actual_tool_results = []
                for item in tools:
                    if isinstance(item, dict) and ('result' in item or 'error' in item) and 'id' in item:
                        actual_tool_results.append(item)
                
                if actual_tool_results:
                    tool_results = actual_tool_results
                    tools = None  # Clear tools so we use saved definitions
                    await self.send_message_to_client(MessageType.LOG, {"message": f"🔧 Received {len(tool_results)} tool results from previous execution"})
                    
                    # Store these tool results for future reference
                    for tool_result in tool_results:
                        if tool_result and isinstance(tool_result, dict) and 'id' in tool_result:
                            self.memory['processed_tool_results'][tool_result['id']] = tool_result
            # Get widget values
            provider_val = self.widget_values.get('provider', self.provider.default)
            model_val = self.widget_values.get('model', self.model.default)
            api_key_val = self.widget_values.get('api_key', self.api_key.default)
            temperature_val = self.widget_values.get('temperature', self.temperature.default)
            max_tokens_val = int(self.widget_values.get('max_tokens', self.max_tokens.default))
            top_p_val = self.widget_values.get('top_p', self.top_p.default)
            use_display_val = self.widget_values.get('use_display_context', self.use_display_context.default)
            display_filter_val = self.widget_values.get('display_context_filter', self.display_context_filter.default)
            use_memory_val = self.widget_values.get('use_runtime_memory', self.use_runtime_memory.default)
            enable_tools_val = self.widget_values.get('enable_tools', self.enable_tools.default)
            output_intermediate_val = self.widget_values.get('output_intermediate_messages', self.output_intermediate_messages.default)

            # Validate inputs
            if not provider_val or not model_val:
                error_msg = "Both provider and model are required"
                await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
                return (error_msg, [])

            # Validate API key
            if not api_key_val:
                error_msg = "API key is required"
                await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
                return (error_msg, [])

            # Build full model string in litellm format
            full_model = f"{provider_val}/{model_val}"

            # Validate provider format (common mistake detection)
            common_models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "claude-3-5-sonnet-20241022", "gemini-1.5-pro"]
            if provider_val in common_models:
                error_msg = f"❌ Provider/Model confusion detected! You entered '{provider_val}' as provider and '{model_val}' as model. Try: Provider='openai' (or 'anthropic', etc.) and Model='{provider_val}'"
                await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
                return (error_msg, [])

            await self.send_message_to_client(MessageType.LOG, {"message": f"🤖 LLM Config: model={full_model}, temp={temperature_val}, max_tokens={max_tokens_val}"})
            await self.send_message_to_client(MessageType.LOG, {"message": f"📋 Context Settings: display={use_display_val} (filter={display_filter_val}), memory={use_memory_val}, tools={enable_tools_val}"})

            # Build messages array - simple approach
            messages = []
            current_prompt_added = 0
            display_message_count = 0
            memory_message_count = 0
            
            # Step 1: Add system prompt
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
                await self.send_message_to_client(MessageType.LOG, {"message": f"📝 Added system prompt ({len(system_prompt)} chars)"})

            # Step 2: Build base messages array ONCE on first run
            if not self.memory['base_messages_built']:
                await self.send_message_to_client(MessageType.LOG, {"message": "🏗️ Building base messages array for first time"})
                
                # Add display context first (historical conversation)
                if use_display_val:
                    # RAW DUMP: Show entire display context before processing
                    raw_context = self.get_display_context()
                    await self.send_message_to_client(MessageType.DEBUG, {"message": f"🔍 RAW DISPLAY CONTEXT DUMP ({len(raw_context)} entries):"})
                    for i, entry in enumerate(raw_context):
                        raw_dump = json.dumps(entry, indent=2)
                        await self.send_message_to_client(MessageType.DEBUG, {"message": f"  RAW[{i}]: {raw_dump}"})
                    
                    # Process display context in chronological order
                    display_messages = await self._get_display_context_messages(display_filter_val, current_prompt=prompt)
                    self.memory['base_messages'].extend(display_messages)
                    display_message_count = len(display_messages)
                    await self.send_message_to_client(MessageType.LOG, {"message": f"💬 Added {display_message_count} messages from display context to base array"})

                # Add runtime memory to base if enabled
                if use_memory_val:
                    memory_messages = self.memory.get('conversation_history', [])
                    self.memory['base_messages'].extend(memory_messages)
                    memory_message_count = len(memory_messages)
                    await self.send_message_to_client(MessageType.LOG, {"message": f"🧠 Added {memory_message_count} messages from runtime memory to base array"})

                # Add current user prompt at the END
                if prompt and not tool_results:
                    user_message = await self._process_multimodal_input(prompt, image, full_model)
                    self.memory['base_messages'].append(user_message)
                    current_prompt_added = 1
                    # Store for execution session
                    self.memory['current_execution_messages'] = [user_message]
                    
                    # Log prompt info
                    prompt_info = f"📝 Added current prompt to base array ({len(prompt)} chars)"
                    if image:
                        if image.startswith('/servable/'):
                            prompt_info += f" + servable image: {image.split('/')[-1]}"
                        elif image.startswith('data:image/'):
                            prompt_info += " + base64 image"
                        elif image.startswith('http'):
                            prompt_info += f" + external image: {image[:50]}..."
                    await self.send_message_to_client(MessageType.LOG, {"message": prompt_info})

                # Mark as built
                self.memory['base_messages_built'] = True
                await self.send_message_to_client(MessageType.LOG, {"message": f"✅ Base messages array built with {len(self.memory['base_messages'])} messages"})

            # Step 3: Use the base messages array
            messages.extend(self.memory['base_messages'])
            current_prompt_added = 1 if any(msg['role'] == 'user' for msg in self.memory['base_messages']) else 0
            
            # Handle tool result continuation - no need to re-add user prompt, it's already in base_messages
            if tool_results:
                await self.send_message_to_client(MessageType.LOG, {"message": "🔧 Using base messages array for tool result continuation"})

            # Add tool results if we received them (AFTER all context)
            tool_results_added = 0
            if tool_results:
                await self.send_message_to_client(MessageType.LOG, {"message": f"🔧 Processing {len(tool_results)} tool results"})
                
                # Get assistant messages and tool results for proper interleaving
                execution_messages = self.memory.get('current_execution_messages', [])
                assistant_messages = [msg for msg in execution_messages if msg['role'] == 'assistant' and msg.get('tool_calls')]
                await self.send_message_to_client(MessageType.DEBUG, {"message": f"🔧 Found {len(assistant_messages)} assistant messages with tool calls in execution session"})
                
                # Fallback to old system if execution session is empty
                if not assistant_messages:
                    pending_message = self.memory.get('pending_tool_calls')
                    if pending_message:
                        assistant_messages = [pending_message]
                        await self.send_message_to_client(MessageType.LOG, {"message": "🔧 Using fallback pending_tool_calls message"})
                    else:
                        await self.send_message_to_client(MessageType.ERROR, {"message": "🔧 ERROR: No assistant messages with tool calls found!"})
                        return ("Error: Tool results received without preceding tool calls", [])
                
                # Create mapping of tool call IDs to tool results (includes ALL processed results)
                tool_result_map = {}
                # Include all previously processed tool results
                tool_result_map.update(self.memory.get('processed_tool_results', {}))
                # Add the current batch
                for tool_result in tool_results:
                    if tool_result and isinstance(tool_result, dict) and 'id' in tool_result:
                        tool_result_map[tool_result['id']] = tool_result
                
                await self.send_message_to_client(MessageType.DEBUG, {"message": f"🔧 Created tool result map with {len(tool_result_map)} results"})
                
                # Interleave assistant messages with their corresponding tool results
                for assistant_msg in assistant_messages:
                    # Add the assistant message
                    messages.append(assistant_msg)
                    tool_results_added += 1
                    await self.send_message_to_client(MessageType.LOG, {"message": f"🔧 Added assistant message with {len(assistant_msg.get('tool_calls', []))} tool calls"})
                    
                    # Add tool results for this assistant message immediately after
                    tool_calls = assistant_msg.get('tool_calls', [])
                    for tool_call in tool_calls:
                        tool_call_id = tool_call.get('id')
                        if tool_call_id and tool_call_id in tool_result_map:
                            tool_result = tool_result_map[tool_call_id]
                            tool_message = {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": json.dumps(tool_result.get('result', tool_result.get('error', 'Unknown result')))
                            }
                            messages.append(tool_message)
                            tool_results_added += 1
                            await self.send_message_to_client(MessageType.DEBUG, {"message": f"🔧 Added tool result for call ID {tool_call_id}"})
                
                await self.send_message_to_client(MessageType.LOG, {"message": f"🔧 Added {tool_results_added} tool-related messages (assistant messages + tool results)"})
                
                # Also add tool results to runtime memory for proper context preservation
                if use_memory_val:
                    for tool_result in tool_results:
                        if tool_result and isinstance(tool_result, dict) and 'id' in tool_result:
                            tool_message = {
                                "role": "tool",
                                "tool_call_id": tool_result['id'],
                                "content": json.dumps(tool_result.get('result', tool_result.get('error', 'Unknown result')))
                            }
                            self.memory['conversation_history'].append(tool_message)
                    await self.send_message_to_client(MessageType.LOG, {"message": f"💾 Added {len(tool_results)} tool result messages to runtime memory"})

            # Show final message breakdown for debugging
            actual_count = len(messages)
            user_msgs = sum(1 for m in messages if m['role'] == 'user')
            assistant_msgs = sum(1 for m in messages if m['role'] == 'assistant') 
            system_msgs = sum(1 for m in messages if m['role'] == 'system')
            tool_msgs = sum(1 for m in messages if m['role'] == 'tool')
            
            await self.send_message_to_client(MessageType.LOG, {"message": f"📊 Total messages to send: {actual_count}"})
            await self.send_message_to_client(MessageType.DEBUG, {"message": f"📋 Final breakdown: {user_msgs} user, {assistant_msgs} assistant, {system_msgs} system, {tool_msgs} tool = {user_msgs + assistant_msgs + system_msgs + tool_msgs} total"})

            # Prepare tool definitions
            tool_definitions = None
            if enable_tools_val:
                if tools:
                    # Fresh tool definitions from dependency pull
                    tool_definitions = self._prepare_tool_definitions(tools)
                    # Save to memory for future runs
                    self.memory['tool_definitions'] = tool_definitions
                    await self.send_message_to_client(MessageType.LOG, {"message": f"🔧 Prepared {len(tool_definitions)} fresh tool definitions"})
                elif self.memory['tool_definitions']:
                    # Use saved tool definitions from previous run
                    tool_definitions = self.memory['tool_definitions']
                    await self.send_message_to_client(MessageType.LOG, {"message": f"🔧 Using {len(tool_definitions)} saved tool definitions from memory"})

            # Set API key for provider
            self._set_api_key(provider_val, api_key_val)
            await self.send_message_to_client(MessageType.LOG, {"message": f"🔑 Set API key for provider: {provider_val}"})

            # Make LLM call
            await self.send_message_to_client(MessageType.LOG, {"message": f"🚀 Calling {full_model}..."})
            
            # DEBUG: Dump the actual messages array
            await self.send_message_to_client(MessageType.DEBUG, {"message": f"📨 MESSAGES ARRAY DUMP ({len(messages)} messages):"})
            for i, msg in enumerate(messages):
                await self.send_message_to_client(MessageType.DEBUG, {"message": f"  MSG[{i}]: {json.dumps(msg, indent=2)}"})
            await self.send_message_to_client(MessageType.DEBUG, {"message": "📨 END MESSAGES DUMP"})
            
            response = await litellm.acompletion(
                model=full_model,
                messages=messages,
                temperature=temperature_val,
                max_tokens=max_tokens_val,
                top_p=top_p_val,
                tools=tool_definitions if tool_definitions else None
            )

            # Extract response
            response_content = response.choices[0].message.content or ""
            tool_calls = response.choices[0].message.tool_calls or []

            await self.send_message_to_client(MessageType.LOG, {"message": f"✅ LLM response received ({len(response_content)} chars, {len(tool_calls)} tool calls)"})
            
            # Log tool calls if any
            if tool_calls:
                tool_names = [tc.function.name if hasattr(tc, 'function') and hasattr(tc.function, 'name') else 'unknown' for tc in tool_calls]
                await self.send_message_to_client(MessageType.LOG, {"message": f"🔧 Tool calls requested: {', '.join(tool_names)}"})

            # Process tool calls
            tool_call_outputs = []
            if tool_calls and enable_tools_val:
                try:
                    tool_call_outputs = await self._process_tool_calls(tool_calls)
                    await self.send_message_to_client(MessageType.LOG, {"message": f"🔧 Processed {len(tool_calls)} tool calls"})
                except Exception as e:
                    await self.send_message_to_client(MessageType.ERROR, {"message": f"🔧 Error in _process_tool_calls: {e}"})
                    tool_call_outputs = []
                
                # Log tool execution results
                executed_tools = sum(1 for output in tool_call_outputs if output is not None)
                await self.send_message_to_client(MessageType.LOG, {"message": f"🔧 Executed {executed_tools} tools successfully"})
                
                # Store the assistant message with tool calls for the next execution
                try:
                    tool_calls_data = []
                    for i, tc in enumerate(tool_calls):
                        try:
                            tool_call_data = {
                                "id": tc.id,
                                "type": "function", 
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            tool_calls_data.append(tool_call_data)
                        except Exception as e:
                            await self.send_message_to_client(MessageType.ERROR, {"message": f"🔧 Error creating tool call data {i}: {e}"})
                            tool_calls_data.append({
                                "id": f"error_call_{i}",
                                "type": "function",
                                "function": {"name": "error", "arguments": "{}"}
                            })
                    
                    assistant_message = {
                        "role": "assistant", 
                        "content": response_content,
                        "tool_calls": tool_calls_data
                    }
                except Exception as e:
                    await self.send_message_to_client(MessageType.ERROR, {"message": f"🔧 Error creating assistant message: {e}"})
                    assistant_message = {
                        "role": "assistant",
                        "content": response_content,
                        "tool_calls": []
                    }
                # Store assistant message in current execution session
                if 'current_execution_messages' not in self.memory:
                    self.memory['current_execution_messages'] = []
                self.memory['current_execution_messages'].append(assistant_message)
                
                # Also add to runtime memory if enabled for proper context preservation
                if use_memory_val:
                    if 'conversation_history' not in self.memory:
                        self.memory['conversation_history'] = []
                    self.memory['conversation_history'].append(assistant_message)
                    await self.send_message_to_client(MessageType.LOG, {"message": f"💾 Added assistant message with tool calls to runtime memory"})
                
                # Also keep the old system for backward compatibility
                self.memory['pending_tool_calls'] = assistant_message
                await self.send_message_to_client(MessageType.LOG, {"message": f"💾 Stored assistant message with {len(tool_calls)} tool calls in execution session"})
                
                # Prepare intermediate message for potential output
                final_intermediate = response_content
                if use_display_val and display_filter_val == "user_and_self" and response_content.strip():
                    final_intermediate = f"Chat: {response_content}"
                
                # Handle intermediate message output when making tool calls
                if output_intermediate_val and response_content.strip():
                    await self.send_message_to_client(MessageType.LOG, {"message": f"📤 Outputting intermediate message before tool calls ({len(response_content)} chars)"})
                    if use_display_val and display_filter_val == "user_and_self":
                        await self.send_message_to_client(MessageType.LOG, {"message": "🏷️ Added 'Chat:' prefix to intermediate message for self-filtering"})
                else:
                    await self.send_message_to_client(MessageType.LOG, {"message": "🚫 Skipping response output due to tool calls"})
                
                # Update waiting behavior: wait for only the tools that were called
                wait_for_inputs = []
                
                # Determine which tool array indices were called
                tool_definitions = self.memory.get('tool_definitions', [])
                tool_name_to_index = {tool['function']['name']: i for i, tool in enumerate(tool_definitions)}
                
                called_tool_indices = set()
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    if tool_name in tool_name_to_index:
                        called_tool_indices.add(tool_name_to_index[tool_name])
                
                # Wait for the specific tool array slots that were called
                for index in called_tool_indices:
                    wait_for_inputs.append(f'tools_{index}')
                
                state_update = NodeStateUpdate(wait_for_inputs=wait_for_inputs, do_wait_inputs=wait_for_inputs)
                await self.send_message_to_client(MessageType.LOG, {"message": f"🔄 Updated node to wait for called tools: {wait_for_inputs} (with do_wait override)"})
                
                # Filter out None values to prevent unnecessary tool executions
                filtered_tool_outputs = []
                for output in tool_call_outputs:
                    if output is not None:
                        filtered_tool_outputs.append(output)
                    else:
                        filtered_tool_outputs.append(SKIP_OUTPUT)
                
                # Return intermediate message if enabled, otherwise skip output
                if output_intermediate_val and response_content.strip():
                    return ((final_intermediate, filtered_tool_outputs), state_update)
                else:
                    return ((SKIP_OUTPUT, filtered_tool_outputs), state_update)

            # Store conversation in memory
            if use_memory_val:
                if prompt:
                    self.memory['conversation_history'].append({"role": "user", "content": prompt})
                self.memory['conversation_history'].append({"role": "assistant", "content": response_content})
                await self.send_message_to_client(MessageType.LOG, {"message": f"💾 Stored conversation in memory (total: {len(self.memory['conversation_history'])} messages)"})
            
            # Clear pending tool calls, execution session, and processed tool results since we're not making any more tool calls
            self.memory['pending_tool_calls'] = None
            self.memory['current_execution_messages'] = []
            self.memory['processed_tool_results'] = {}
            # Reset for next workflow run
            self.memory['base_messages_built'] = False
            self.memory['base_messages'] = []
            await self.send_message_to_client(MessageType.LOG, {"message": "🧹 Cleared execution session - no more tool calls"})
            
            # Add Chat: prefix for self-filtering when display context is enabled with user_and_self filter
            final_response = response_content
            if use_display_val and display_filter_val == "user_and_self" and response_content.strip():
                final_response = f"Chat: {response_content}"
                await self.send_message_to_client(MessageType.LOG, {"message": "🏷️ Added 'Chat:' prefix for self-filtering"})
            
            return (final_response, tool_call_outputs)

        except Exception as e:
            error_msg = f"LLM error: {str(e)}"
            await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
            return (error_msg, [])

    async def _get_display_context_messages(self, filter_mode: str, current_prompt: str = None) -> List[Dict[str, Any]]:
        """Extract and convert display context to chat messages."""
        display_context = self.get_display_context()
        messages = []
        
        self_node_id = self.node_info.get('id')
        
        await self.send_message_to_client(MessageType.DEBUG, {"message": f"🔍 FILTERING: mode='{filter_mode}', self_node_id={self_node_id}, context_entries={len(display_context)}"})
        
        # Find the most recent user message that matches current prompt (if any)
        most_recent_duplicate_index = -1
        if current_prompt:            
            for i in reversed(range(len(display_context))):
                entry = display_context[i]
                node_title = entry.get('node_title', '')
                content = entry.get('data', '')
                if ((node_title == "User" or 'DisplayInputEventNode' in node_title) and 
                    content == current_prompt):
                    most_recent_duplicate_index = i
                    break
        
        for i, entry in enumerate(display_context):
            node_id = entry.get('node_id')
            node_title = entry.get('node_title', '')
            content = entry.get('data', '')
            
            # Skip only the most recent duplicate to preserve conversation history
            if i == most_recent_duplicate_index:
                continue
            
            
            # Apply filtering
            if filter_mode == "user_and_self":
                # Include user inputs and LLM chat responses (with Chat: prefix)
                if node_title == "User" or 'DisplayInputEventNode' in node_title:
                    messages.append({"role": "user", "content": content})
                elif content.startswith("Chat: "):
                    # Remove the "Chat: " prefix and add as assistant message
                    chat_content = content[6:]  # Remove "Chat: "
                    messages.append({"role": "assistant", "content": chat_content})
                elif node_id == self_node_id:
                    messages.append({"role": "assistant", "content": content})
            elif filter_mode == "all":
                # Include all context, map node types to roles
                if node_title == "User" or 'DisplayInputEventNode' in node_title:
                    messages.append({"role": "user", "content": content})
                else:
                    messages.append({"role": "assistant", "content": content})
        
        await self.send_message_to_client(MessageType.DEBUG, {"message": f"🔍 FILTERING RESULT: {len(messages)} messages after filtering"})
        return messages

    async def _process_multimodal_input(self, prompt: str, image: str = None, model: str = "") -> Dict[str, Any]:
        """
        Process input that may contain images for vision-capable models.
        Priority: dedicated image socket > embedded base64 in prompt
        Supports servable URLs, external URLs, and base64 data URLs.
        """
        await self.send_message_to_client(MessageType.DEBUG, {"message": f"🖼️ _process_multimodal_input called with: prompt='{str(prompt)}', image='{image}', model='{model}'"})
        
        # Vision-capable models
        vision_models = [
            "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4-vision-preview",
            "claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-5-haiku-latest",
            "gemini-1.5-pro", "gemini-1.5-flash"
        ]
        
        # Only process images for vision-capable models
        model_name = model.split('/')[-1] if '/' in model else model
        await self.send_message_to_client(MessageType.DEBUG, {"message": f"🖼️ Model name extracted: '{model_name}', is vision capable: {model_name in vision_models}"})
        
        if model_name not in vision_models:
            await self.send_message_to_client(MessageType.DEBUG, {"message": "🖼️ Model not vision-capable, returning text-only message"})
            return {"role": "user", "content": prompt}
        
        image_url = None
        
        # Priority 1: Dedicated image socket
        if image:
            await self.send_message_to_client(MessageType.DEBUG, {"message": f"🖼️ Processing dedicated image socket: '{image}'"})
            if image.startswith('/servable/'):
                # Convert servable path to full URL
                image_url = f"http://localhost:8000{image}"
                await self.send_message_to_client(MessageType.DEBUG, {"message": f"🖼️ Converted servable path to URL: '{image_url}'"})
            elif image.startswith(('http://', 'https://')):
                # External URL - use directly
                image_url = image
                await self.send_message_to_client(MessageType.DEBUG, {"message": f"🖼️ Using external URL directly: '{image_url}'"})
            elif image.startswith('data:image/'):
                # Base64 data URL - use directly
                image_url = image
                await self.send_message_to_client(MessageType.DEBUG, {"message": f"🖼️ Using base64 data URL (length: {len(image)})"})
            else:
                # Assume it's a filename in servable folder
                image_url = f"http://localhost:8000/servable/{image}"
                await self.send_message_to_client(MessageType.DEBUG, {"message": f"🖼️ Assumed filename, converted to URL: '{image_url}'"})
        
        # Priority 2: Check for embedded image links in prompt (fallback)
        else:
            await self.send_message_to_client(MessageType.DEBUG, {"message": "🖼️ No dedicated image, checking for embedded images in prompt"})
            extracted_url, cleaned_prompt = self._extract_image_from_prompt(str(prompt))
            if extracted_url:
                image_url = extracted_url
                prompt = cleaned_prompt  # Use the cleaned prompt without image syntax
                await self.send_message_to_client(MessageType.DEBUG, {"message": f"🖼️ Found embedded image: '{extracted_url}', cleaned prompt: '{cleaned_prompt}'"})
        
        # Create multimodal message if we have an image
        if image_url:
            content = [
                {"type": "text", "text": str(prompt).strip() if str(prompt).strip() else "Analyze this image:"},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
            await self.send_message_to_client(MessageType.DEBUG, {"message": f"🖼️ Created multimodal message with image URL: '{image_url}'"})
            return {"role": "user", "content": content}
        
        # Text-only fallback
        await self.send_message_to_client(MessageType.DEBUG, {"message": "🖼️ No image found, returning text-only message"})
        return {"role": "user", "content": str(prompt)}

    def _extract_image_from_prompt(self, prompt: str):
        """
        Extract the first image link found in prompt text and return (image_url, cleaned_prompt).
        Supports markdown images, HTML images, direct URLs, servable links, and base64 data URLs.
        Returns (None, original_prompt) if no image found.
        """
        import re
        
        # Same patterns as ImageLinkExtractNode
        patterns = [
            # Markdown images: ![alt text](url)
            r'!\[([^\]]*)\]\(([^)]+)\)',
            # HTML images: <img src="url" ...>
            r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>',
            # Direct image URLs
            r'(https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp|bmp|svg)(?:\?[^\s]*)?)',
            # Servable links
            r'(/servable/[^\s]+)',
            # Data URLs for images
            r'(data:image/[^;]+;base64,[A-Za-z0-9+/=]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    # Markdown format: (alt_text, url)
                    extracted_url = match.group(2)
                else:
                    # Direct URL match
                    extracted_url = match.group(1)
                
                # Remove the image syntax from prompt
                cleaned_prompt = prompt[:match.start()] + prompt[match.end():]
                cleaned_prompt = cleaned_prompt.strip()
                
                # Process the extracted URL
                if extracted_url.startswith('/servable/'):
                    # Convert servable path to full URL
                    processed_url = f"http://localhost:8000{extracted_url}"
                elif extracted_url.startswith(('http://', 'https://')):
                    # External URL - use directly (LiteLLM will handle download if needed)
                    processed_url = extracted_url
                elif extracted_url.startswith('data:image/'):
                    # Base64 data URL - use directly
                    processed_url = extracted_url
                else:
                    # Assume it's a filename in servable folder
                    processed_url = f"http://localhost:8000/servable/{extracted_url}"
                
                return processed_url, cleaned_prompt
        
        # No image found
        return None, prompt

    def _prepare_tool_definitions(self, tools: List[Any]) -> List[Dict[str, Any]]:
        """Convert tool inputs to litellm-compatible tool definitions."""
        tool_definitions = []
        
        for tool in tools:
            if isinstance(tool, dict) and 'name' in tool:
                tool_def = {
                    "type": "function",
                    "function": {
                        "name": tool['name'],
                        "description": tool.get('description', ''),
                        "parameters": tool.get('input_schema', {})
                    }
                }
                tool_definitions.append(tool_def)
        
        return tool_definitions

    async def _process_tool_calls(self, tool_calls: List[Any]) -> List[Dict[str, Any]]:
        """Process tool calls from LLM response into MCP-compatible format and route to correct tools."""
        # Get the tool definitions to map names to array indices
        tool_definitions = self.memory.get('tool_definitions', [])
        tool_name_to_index = {tool['function']['name']: i for i, tool in enumerate(tool_definitions)}
        
        # Create array to hold tool calls for each tool (matching array size)
        processed_calls = [None] * len(tool_definitions) if tool_definitions else []
        
        for i, tool_call in enumerate(tool_calls):
            try:
                
                # Extract data with explicit error handling
                try:
                    call_id = tool_call.id
                except Exception as e:
                    await self.send_message_to_client(MessageType.ERROR, {"message": f"🔧 Error accessing tool_call.id: {e}"})
                    call_id = f"unknown_id_{i}"
                
                try:
                    call_name = tool_call.function.name
                except Exception as e:
                    await self.send_message_to_client(MessageType.ERROR, {"message": f"🔧 Error accessing tool_call.function.name: {e}"})
                    call_name = "unknown_name"
                
                try:
                    call_args = json.loads(tool_call.function.arguments)
                except Exception as e:
                    await self.send_message_to_client(MessageType.ERROR, {"message": f"🔧 Error accessing tool_call.function.arguments: {e}"})
                    call_args = {}
                
                call_data = {
                    "id": call_id,
                    "name": call_name,
                    "arguments": call_args
                }
                
                # Route to correct array index based on tool name
                tool_name = call_data["name"]
                if tool_name in tool_name_to_index:
                    index = tool_name_to_index[tool_name]
                    processed_calls[index] = call_data
                else:
                    # If tool name not found, put it in first available slot
                    if processed_calls:
                        processed_calls[0] = call_data
                        await self.send_message_to_client(MessageType.LOG, {"message": f"🔧 Warning: Tool '{tool_name}' not found in mapping, using fallback"})
                        
            except Exception as e:
                error_call = {"error": f"Failed to process tool call: {str(e)}"}
                await self.send_message_to_client(MessageType.ERROR, {"message": f"🔧 Tool call processing error: {str(e)}"})
                if processed_calls:
                    processed_calls[0] = error_call
        
        return processed_calls

    def _set_api_key(self, provider: str, api_key: str):
        """Set the API key for the specified provider."""
        if provider == "openai":
            litellm.openai_key = api_key
        elif provider == "anthropic":
            litellm.anthropic_key = api_key
        elif provider == "vertex_ai":
            litellm.vertex_ai_project = None  # Will use api_key as token
            litellm.vertex_ai_location = None
        elif provider == "together_ai":
            litellm.togetherai_api_key = api_key
        elif provider == "groq":
            litellm.groq_api_key = api_key
        else:
            # For other providers, set the general api_key
            litellm.api_key = api_key