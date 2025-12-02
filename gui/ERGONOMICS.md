# GUI Ergonomics Features

This document describes the ergonomics improvements added to the Py3plex GUI to enhance user experience and productivity.

## Command Palette (Ctrl+K)

The GUI includes a command palette for quick access to all features. Press `Ctrl+K` (or `Cmd+K` on Mac) to open the command palette at any time.

### Features

- **Fuzzy search**: Type to filter commands by name or category
- **Keyboard navigation**: Use arrow keys to navigate, Enter to execute
- **Categories**: Commands are organized into Navigation, Analysis, Export, View, and Help
- **Disabled states**: Commands that require prerequisites (like a loaded graph) are shown as disabled

### Available Commands

| Command | Shortcut | Category |
|---------|----------|----------|
| Go to Load Data | Ctrl+1 | Navigation |
| Go to Visualize | Ctrl+2 | Navigation |
| Go to Analyze | Ctrl+3 | Navigation |
| Go to Export | Ctrl+4 | Navigation |
| Toggle Dark Mode | - | View |
| Open Job Monitor | - | View |
| Show Keyboard Shortcuts | Ctrl+/ | Help |
| Open Documentation | - | Help |

## Dark Mode

The GUI supports three theme modes:

- **Light**: Default light theme
- **Dark**: Dark theme with reduced eye strain
- **System**: Automatically follows your operating system's preference

### Using Dark Mode

- Click the theme toggle button in the navigation bar (sun/moon/monitor icon)
- Each click cycles through: Light → Dark → System → Light
- Your preference is saved and persists across sessions

## Keyboard Shortcuts

The GUI includes comprehensive keyboard shortcuts for common actions. Press `Ctrl+/` (or `Cmd+/` on Mac) to view the shortcuts help panel at any time.

### Global Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` | Open command palette |
| `Ctrl+/` | Toggle keyboard shortcuts help panel |
| `Escape` | Close modals and clear errors |

### Load Data Page

| Shortcut | Action |
|----------|--------|
| `Ctrl+U` | Open file picker dialog |
| `Ctrl+Enter` | Upload and parse the selected file |
| `Escape` | Clear file selection and error messages |

### Analyze Page

| Shortcut | Action |
|----------|--------|
| `Ctrl+L` | Run layout computation |
| `Ctrl+Shift+C` | Run centrality analysis |
| `Ctrl+D` | Run community detection |
| `Shift+Delete` | Clear completed and failed jobs |

### Export Page

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Save workspace bundle |
| `Ctrl+1` | Download centrality CSV |
| `Ctrl+2` | Download community JSON |
| `Ctrl+3` | Download layout positions JSON |

## Toast Notifications

The GUI uses toast notifications for important feedback:

- **Success**: Green background, indicates successful operations
- **Error**: Red background, indicates failures
- **Warning**: Yellow background, indicates potential issues
- **Info**: Blue background, informational messages

Toasts appear in the bottom-right corner and automatically dismiss after 4 seconds. Click the X button to dismiss early.

## Tooltips

All interactive elements (buttons, icons, inputs) include context-sensitive tooltips that appear on hover. Tooltips provide:

- Action descriptions
- Keyboard shortcut hints
- Additional context about features
- Usage tips

## Recent Files

The Load Data page maintains a history of recently uploaded files (up to 5 most recent). Features include:

- Quick reload of previously uploaded files
- Displays file metadata (nodes, edges, upload date)
- One-click restoration without re-uploading
- Persists across browser sessions (stored in localStorage)

## Search and Filter

The results table component (used for displaying analysis results) includes:

- **Search**: Filter results by any column value
- **Sort**: Click column headers to sort ascending/descending
- **Result count**: Shows number of matching results
- **Clear**: Quick button to clear search query

## Loading Indicators

Enhanced loading states provide better feedback:

- **Spinner animations**: Visual indication of background processing
- **Progress messages**: Clear descriptions of current operations
- **Adaptive polling**: Faster updates for running jobs, slower for queued
- **Completion notifications**: Toast messages when jobs finish

## Clear Completed Jobs

The Job Center includes a "Clear Done" button to remove:

- Completed jobs
- Failed jobs
- Keeps active (queued/running) jobs visible

Keyboard shortcut: `Shift+Delete`

## UI Improvements

### Inline Help

- Keyboard shortcut hints shown directly in the UI (e.g., "Ctrl+U" near upload button)
- Tips and suggestions in empty states
- Contextual help icons with detailed explanations

### Better Empty States

- Helpful messages when no data is present
- Quick navigation links to relevant pages
- Tips for getting started

### Improved Error Messages

- Clear, actionable error descriptions
- Visual distinction between validation errors and system errors
- Suggestions for fixing common issues

## Accessibility

All ergonomic features follow accessibility best practices:

- **Keyboard navigation**: All actions accessible via keyboard
- **ARIA labels**: Screen reader support for all interactive elements
- **Focus management**: Logical tab order and visible focus indicators
- **Color contrast**: WCAG AA compliant color schemes
- **Dark mode**: Reduces eye strain in low-light conditions

## Component Documentation

### Custom React Hooks

#### `useKeyboardShortcuts`

```typescript
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';

const shortcuts = [
  {
    key: 'u',
    ctrl: true,
    action: () => console.log('Ctrl+U pressed'),
    description: 'Open file picker'
  }
];

useKeyboardShortcuts(shortcuts);
```

#### `useCommandPalette`

```typescript
import { useCommandPalette, Command } from '../hooks/useCommandPalette';

const commands: Command[] = [
  {
    id: 'nav-home',
    label: 'Go to Home',
    shortcut: 'Ctrl+1',
    category: 'navigation',
    action: () => navigate('/'),
  }
];

const { isOpen, query, setQuery, groupedCommands, executeCommand, close } = 
  useCommandPalette({ commands });
```

#### `useDarkMode`

```typescript
import { useDarkMode } from '../hooks/useDarkMode';

const { theme, isDark, setTheme, toggleTheme } = useDarkMode();

// Toggle between light/dark/system
<button onClick={toggleTheme}>Toggle Theme</button>
```

#### `useToasts`

```typescript
import { useToasts } from '../hooks/useToasts';

const { toasts, success, error, warning, info, removeToast } = useToasts();

// Show notifications
success('File uploaded successfully!');
error('Failed to process file');
```

### Reusable Components

#### `<CommandPalette>`

```typescript
<CommandPalette
  isOpen={isOpen}
  query={query}
  setQuery={setQuery}
  groupedCommands={groupedCommands}
  onExecute={executeCommand}
  onClose={close}
/>
```

#### `<ThemeToggle>`

```typescript
<ThemeToggle theme={theme} onToggle={toggleTheme} />
```

#### `<ToastContainer>`

```typescript
<ToastContainer toasts={toasts} onRemove={removeToast} />
```

#### `<Tooltip>`

```typescript
<Tooltip content="This is a helpful tooltip">
  <button>Hover me</button>
</Tooltip>
```

#### `<ShortcutsHelp>`

```typescript
<ShortcutsHelp shortcuts={shortcuts} />
```

#### `<SearchBar>`

```typescript
<SearchBar 
  placeholder="Search results..."
  onSearch={(query) => console.log(query)}
/>
```

#### `<LoadingProgress>`

```typescript
<LoadingProgress 
  message="Processing..."
  progress={45}  // Optional: 0-100
/>
```

#### `<ResultsTable>`

```typescript
const columns = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'value', label: 'Value', sortable: true }
];

const data = [
  { name: 'Node1', value: 0.85 },
  { name: 'Node2', value: 0.92 }
];

<ResultsTable 
  columns={columns}
  data={data}
  searchPlaceholder="Search nodes..."
/>
```

## Browser Compatibility

All ergonomics features are tested and supported on:

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Performance Considerations

- **Debounced search**: Search queries are processed efficiently
- **Memoized filtering**: Large datasets are filtered without lag
- **Lazy rendering**: Only visible elements are rendered
- **Optimized polling**: Job status checks use adaptive intervals
- **Smooth transitions**: Theme changes use CSS transitions for better UX

## Future Enhancements

Planned ergonomics improvements:

- Customizable keyboard shortcuts
- Undo/redo for workspace changes
- Drag-and-drop rearrangement of panels
- Session restoration (recover unsaved work)
- More keyboard shortcuts for common operations

## Feedback

Have suggestions for ergonomics improvements? Please open an issue on GitHub with the `enhancement` and `gui` labels.
