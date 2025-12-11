import asyncio
import logging
from asyncio import StreamReader, StreamWriter

_LOGGER = logging.getLogger(__name__)

class OreiMatrixClient:
    """Async client for controlling Orei HDMI Matrix via Telnet."""

    def __init__(self, host, port=23) -> None:
        self._host = host
        self._port = port
        self._reader: StreamReader | None = None
        self._writer: StreamWriter | None = None
        self._lock = asyncio.Lock()

    # -----------------------
    # Connection management
    # -----------------------

    async def connect(self):
        """Establish a TCP connection to the matrix."""
        try:
            self._reader, self._writer = await asyncio.open_connection(
                self._host, self._port
            )
            _LOGGER.debug("Connected to Orei Matrix at %s:%s", self._host, self._port)
        except Exception as e:
            _LOGGER.error("Failed to connect to Orei Matrix: %s", e)
            raise

    async def disconnect(self):
        """Close the connection."""
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
            self._reader = None
            self._writer = None
            _LOGGER.debug("Disconnected from Orei Matrix")

    async def _ensure_connected(self):
        """Reconnect if needed."""
        if not self._writer or self._writer.is_closing():
            await self.connect()

    # -----------------------
    # Core command handling
    # -----------------------

    async def _send_command_multiple(self, cmd: str) -> list[str]:
        async with self._lock:
            await self._ensure_connected()

            # Sanity check: _ensure_connected should have set these
            if self._reader is None or self._writer is None:
                raise RuntimeError("Connection not established")

            try:
                _LOGGER.debug("Sending command: %s", cmd)
                self._writer.write((cmd + "\r\n").encode("ascii"))
                await self._writer.drain()

                # Read response until idle
                chunks = bytearray()
                try:
                    while True:
                        data = await asyncio.wait_for(
                            self._reader.read(1024), timeout=0.3
                        )
                        if not data:
                            break
                        chunks.extend(data)
                except asyncio.TimeoutError:
                    pass

                if not chunks:
                    _LOGGER.warning("No response received for command: %s", cmd)
                    return [""]

                # --- Clean and parse ---
                filtered = bytes(b for b in chunks if b < 0x80)
                text = filtered.decode("ascii", errors="ignore").strip()

                # Split into lines, remove empty and banner/prompt lines
                lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
                _LOGGER.debug("Parsed lines: %s", lines)

                # Remove echoed command and banner
                cleaned = []
                for line in lines:
                    if (
                        line.startswith(cmd.split()[0]) or
                        line.startswith("********") or
                        line.startswith("FW Version") or
                        line == ">" or
                        "Welcome" in line
                    ):
                        continue
                    cleaned.append(line.strip('>'))

                return cleaned

            except Exception as e:
                _LOGGER.warning("Telnet command failed (%s), reconnecting", e)
                await self.disconnect()
                raise

    async def _send_command(self, cmd: str) -> str:
        cleaned = await self._send_command_multiple(cmd)
        response = cleaned[-1] if cleaned else ""
        _LOGGER.debug("Cleaned response: %s", response)
        return response

    # -----------------------
    # Matrix control commands
    # -----------------------

    async def get_type(self) -> str:
        """Return matrix model type."""
        return await self._send_command("r type!")

    async def get_power(self) -> bool:
        """Return True if matrix power is ON."""
        res = await self._send_command("r power!")
        return "on" in res.lower()

    async def set_power(self, state: bool):
        """Turn matrix power ON or OFF."""
        cmd = f"s power {1 if state else 0}!"
        await self._send_command(cmd)

    async def get_output_source(self, output_id: int):
        """Get the current input assigned to a given output."""
        res = await self._send_command(f"r av out {output_id}!")
        _LOGGER.debug("Parsing output source response: %s", res)

        res = res.lower().replace("->", " -> ").replace(":", " ")
        parts = res.split()
        input_id = None

        try:
            for i, token in enumerate(parts):
                if token in ("input", "in") and i + 1 < len(parts):
                    input_id = int(parts[i + 1])
        except ValueError:
            _LOGGER.warning("Could not parse integers from response: %s", res)
            return None

        return input_id

    async def get_output_sources(self):
        """Get the current input assigned to a given output."""
        results = await self._send_command_multiple(f"r av out 0!")
        response = {}

        for res in results:
            res = res.lower().replace("->", " -> ").replace(":", " ")
            parts = res.split()
            output_id = None
            input_id = None

            try:
                for i, token in enumerate(parts):
                    if token in ("output", "out") and i + 1 < len(parts):
                        output_id = int(parts[i + 1])
                    if token in ("input", "in") and i + 1 < len(parts):
                        input_id = int(parts[i + 1])
                response[output_id] = input_id
            except ValueError:
                _LOGGER.warning("Could not parse integers from response: %s", res)
                return None
        return response

    async def get_in_link(self, input_id: int):
        """Get the input state."""
        res = await self._send_command(f"r link in {input_id}!")
        return not "disconnect" in res.lower()

    async def get_in_links(self):
        """Get the input state."""
        results = await self._send_command_multiple(f"r link in 0!")
        response = {}

        for res in results:
            res = res.lower().replace(":", " ")
            parts = res.split()
            input_id = None

            try:
                for i, token in enumerate(parts):
                    if token in ("input", "in") and i + 1 < len(parts):
                        input_id = int(parts[i + 1])
                response[input_id] = not "disconnect" in res
            except ValueError:
                _LOGGER.warning("Could not parse integers from response: %s", res)
                return None
        return response

    async def get_out_link(self, output_id: int):
        """Get the output state."""
        res = await self._send_command(f"r link out {output_id}!")
        return not "disconnect" in res.lower()

    async def get_out_links(self):
        """Get the input state."""
        results = await self._send_command_multiple(f"r link out 0!")
        response = {}

        for res in results:
            res = res.lower().replace(":", " ")
            parts = res.split()
            output_id = None

            try:
                for i, token in enumerate(parts):
                    if token in ("output", "out") and i + 1 < len(parts):
                        output_id = int(parts[i + 1])
                response[output_id] = not "disconnect" in res
            except ValueError:
                _LOGGER.warning("Could not parse integers from response: %s", res)
                return None
        return response

    async def set_cec_in(self, input_id: int, command: str):
        """Send a CEC command to the input."""
        await self._send_command(f"s cec in {input_id} {command}!")

    async def set_cec_out(self, output_id: int, command: str):
        """Send a CEC command to the output."""
        await self._send_command(f"s cec hdmi out {output_id} {command}!")

    async def set_output_source(self, input_id: int, output_id: int):
        """Assign an input to an output."""
        await self._send_command(f"s in {input_id} av out {output_id}!")