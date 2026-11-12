"""In-memory educational filesystem with process-level access control."""
from typing import Dict, List, Optional


class FileSystem:
    def __init__(self):
        self.entries: Dict[str, dict] = {'/': {'type': 'dir', 'owner': 'kernel'}}
        self.log: List[dict] = []
        self.permissions: Dict[str, dict] = {}

    def authorize_process(self, pid: str, allowed_prefixes: List[str], read_only: bool = False):
        """Grant a process access to specific directory prefixes."""
        normalized = tuple(p.rstrip('/') or '/' for p in allowed_prefixes)
        self.permissions[pid] = {
            "prefixes": normalized,
            "read_only": read_only,
        }

    def check_access(self, pid: Optional[str], command: str, path: str) -> None:
        """Verify whether `pid` is authorized to run `command` on `path`."""
        if pid is None or pid == "kernel":
            return
        if pid not in self.permissions:
            raise PermissionError(f"Process {pid} has no file-system permissions registered")

        policy = self.permissions[pid]
        if policy["read_only"] and command not in ("ls", "cat"):
            raise PermissionError(f"Process {pid} has read-only access; '{command}' denied on {path}")

        allowed = any(
            prefix == '/' or path == prefix or path.startswith(prefix + '/')
            for prefix in policy["prefixes"]
        )
        if not allowed:
            raise PermissionError(f"Process {pid} is not authorized to access '{path}'")

    def execute(self, command: str, path: str, content: str = '', pid: Optional[str] = None):
        if command not in ('mkdir', 'ls', 'mkfile', 'write', 'append', 'cat', 'rm', 'rmdir'):
            raise ValueError('Unknown command')
        if (
            not isinstance(path, str)
            or not path.startswith('/')
            or '//' in path
            or any(x in ('.', '..') for x in path.split('/'))
        ):
            raise ValueError('Invalid absolute path')

        path = path.rstrip('/') or '/'
        parent = path.rsplit('/', 1)[0] or '/'

        try:
            self.check_access(pid, command, path)

            if command == 'ls':
                if self.entries.get(path, {}).get('type') != 'dir':
                    raise ValueError('Not a directory')
                result = sorted(
                    p for p in self.entries if p != path and (p.rsplit('/', 1)[0] or '/') == path
                )
            elif command in ('mkdir', 'mkfile'):
                if path in self.entries:
                    raise ValueError('Already exists')
                if self.entries.get(parent, {}).get('type') != 'dir':
                    raise ValueError('Parent directory missing')
                self.entries[path] = (
                    {'type': 'dir', 'owner': pid or 'kernel'}
                    if command == 'mkdir'
                    else {'type': 'file', 'content': '', 'owner': pid or 'kernel'}
                )
                result = 'Created'
            elif command in ('write', 'append', 'cat'):
                if self.entries.get(path, {}).get('type') != 'file':
                    raise ValueError('Not a file')
                if command == 'cat':
                    result = self.entries[path]['content']
                else:
                    self.entries[path]['content'] = (
                        self.entries[path]['content'] if command == 'append' else ''
                    ) + content
                    result = self.entries[path]['content']
            else:
                expected = 'file' if command == 'rm' else 'dir'
                if path == '/' or self.entries.get(path, {}).get('type') != expected:
                    raise ValueError('Wrong type or missing path')
                if expected == 'dir' and any(p.startswith(path + '/') for p in self.entries):
                    raise ValueError('Directory not empty')
                del self.entries[path]
                result = 'Removed'

            self.log.append({
                'pid': pid or 'kernel',
                'command': command,
                'path': path,
                'status': 'PASS',
                'result': result,
            })
            return result

        except PermissionError as exc:
            self.log.append({
                'pid': pid or 'kernel',
                'command': command,
                'path': path,
                'status': 'DENIED',
                'result': str(exc),
            })
            raise
        except ValueError as exc:
            self.log.append({
                'pid': pid or 'kernel',
                'command': command,
                'path': path,
                'status': 'FAIL',
                'result': str(exc),
            })
            raise

    def stats(self):
        return {
            'files': sum(e['type'] == 'file' for e in self.entries.values()),
            'directories': sum(e['type'] == 'dir' for e in self.entries.values()),
            'bytes': sum(len(e.get('content', '').encode()) for e in self.entries.values()),
        }
            
