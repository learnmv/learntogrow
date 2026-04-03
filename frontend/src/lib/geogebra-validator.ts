/**
 * GeoGebra Command Validation Utilities
 * Helpers for validating and executing GeoGebra commands safely
 */

import {
  type AppletType,
  GEOGEBRA_COMMANDS,
  getCommandsForApplet,
  isValidCommand,
  isValidApiMethod,
  getCommandsByCategory,
  supports3D,
  findAppletTypesForCommand,
  suggestCommands,
} from './geogebra-commands';

export type { AppletType };

export {
  GEOGEBRA_COMMANDS,
  getCommandsForApplet,
  isValidCommand,
  isValidApiMethod,
  getCommandsByCategory,
  supports3D,
  findAppletTypesForCommand,
  suggestCommands,
};

/**
 * Validation result with details
 */
export interface ValidationResult {
  valid: boolean;
  error?: string;
  suggestions?: string[];
  supportedIn?: AppletType[];
}

/**
 * Validate a command with detailed feedback
 */
export function validateCommand(
  appletType: AppletType,
  command: string
): ValidationResult {
  const isValid = isValidCommand(appletType, command);

  if (isValid) {
    return { valid: true };
  }

  // Find which applets support this command
  const supportedIn = findAppletTypesForCommand(command);

  // Get suggestions
  const suggestions = suggestCommands(appletType, command, 3);

  let error = `Command "${command}" is not available in ${appletType} applet.`;

  if (supportedIn.length > 0) {
    error += ` Available in: ${supportedIn.join(', ')}.`;
  }

  return {
    valid: false,
    error,
    suggestions: suggestions.length > 0 ? suggestions : undefined,
    supportedIn: supportedIn.length > 0 ? supportedIn : undefined,
  };
}

/**
 * Wrapper for safe command execution with validation
 */
export function createSafeEvalCommand(
  appletType: AppletType,
  api: {
    evalCommand: (cmd: string) => void;
    evalCommandGetLabels?: (cmd: string) => string;
  },
  options?: {
    onError?: (error: string, command: string) => void;
    onValidationError?: (result: ValidationResult, command: string) => void;
  }
) {
  return {
    /**
     * Execute a command with validation
     */
    execute(command: string): boolean {
      const validation = validateCommand(appletType, command);

      if (!validation.valid) {
        if (options?.onValidationError) {
          options.onValidationError(validation, command);
        } else if (options?.onError) {
          options.onError(validation.error || 'Invalid command', command);
        }
        return false;
      }

      try {
        api.evalCommand(command);
        return true;
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : String(err);
        if (options?.onError) {
          options.onError(errorMsg, command);
        }
        return false;
      }
    },

    /**
     * Execute and get labels
     */
    executeGetLabels(command: string): string | null {
      const validation = validateCommand(appletType, command);

      if (!validation.valid) {
        if (options?.onValidationError) {
          options.onValidationError(validation, command);
        }
        return null;
      }

      if (!api.evalCommandGetLabels) {
        if (options?.onError) {
          options.onError('evalCommandGetLabels not available', command);
        }
        return null;
      }

      try {
        return api.evalCommandGetLabels(command);
      } catch (err) {
        return null;
      }
    },

    /**
     * Validate without executing
     */
    validate(command: string): ValidationResult {
      return validateCommand(appletType, command);
    },
  };
}

/**
 * Get recommended applet type for a question type
 */
export function getRecommendedApplet(
  questionType: 'algebra' | 'geometry' | 'graphing' | '3d' | 'calculus'
): AppletType {
  switch (questionType) {
    case '3d':
      return '3d';
    case 'geometry':
      return 'geometry';
    case 'calculus':
      return 'cas';
    case 'graphing':
      return 'graphing';
    case 'algebra':
    default:
      return 'graphing';
  }
}

/**
 * Build a command with parameter validation
 */
export function buildCommand(
  baseCommand: string,
  params: (string | number | [number, number] | [number, number, number])[]
): string {
  const formattedParams = params.map(p => {
    if (Array.isArray(p)) {
      return `(${p.join(', ')})`;
    }
    if (typeof p === 'string' && p.includes(' ')) {
      return `"${p}"`;
    }
    return String(p);
  });

  return `${baseCommand}(${formattedParams.join(', ')})`;
}

/**
 * Parse a command string to extract command name and parameters
 */
export function parseCommand(commandString: string): {
  command: string;
  params: string[];
} | null {
  const match = commandString.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)\s*$/);

  if (!match) {
    // Check for function notation like f(x) = ...
    const funcMatch = commandString.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\(([a-zA-Z,\s]+)\)\s*=\s*(.+)$/);
    if (funcMatch) {
      return {
        command: funcMatch[1],
        params: [funcMatch[3]], // The expression after =
      };
    }

    // Check for simple assignment like A = (1, 2)
    const assignMatch = commandString.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)$/);
    if (assignMatch) {
      return {
        command: 'SetValue',
        params: [assignMatch[1], assignMatch[2]],
      };
    }

    return null;
  }

  const command = match[1];
  const paramsStr = match[2];

  // Simple split (doesn't handle nested parentheses perfectly)
  const params = paramsStr
    .split(',')
    .map(p => p.trim())
    .filter(p => p.length > 0);

  return { command, params };
}

/**
 * Command builder for fluent API
 */
export class CommandBuilder {
  private commands: string[] = [];
  private appletType: AppletType;

  constructor(appletType: AppletType) {
    this.appletType = appletType;
  }

  /**
   * Add a command
   */
  add(command: string): this {
    this.commands.push(command);
    return this;
  }

  /**
   * Add a point
   */
  point(name: string, x: number, y: number, z?: number): this {
    const coords = z !== undefined ? `${x}, ${y}, ${z}` : `${x}, ${y}`;
    this.commands.push(`${name} = (${coords})`);
    return this;
  }

  /**
   * Add a line through two points
   */
  line(name: string, point1: string, point2: string): this {
    this.commands.push(`${name} = Line(${point1}, ${point2})`);
    return this;
  }

  /**
   * Add a circle
   */
  circle(name: string, center: string, radius: number | string): this {
    this.commands.push(`${name} = Circle(${center}, ${radius})`);
    return this;
  }

  /**
   * Add a polygon
   */
  polygon(name: string, ...points: string[]): this {
    this.commands.push(`${name} = Polygon(${points.join(', ')})`);
    return this;
  }

  /**
   * Set color for an object
   */
  color(object: string, r: number, g: number, b: number): this {
    this.commands.push(`SetColor(${object}, ${r}, ${g}, ${b})`);
    return this;
  }

  /**
   * Set visibility
   */
  visible(object: string, show: boolean): this {
    this.commands.push(`SetVisible(${object}, ${show})`);
    return this;
  }

  /**
   * Add a function
   */
  function(name: string, expression: string): this {
    this.commands.push(`${name}(x) = ${expression}`);
    return this;
  }

  /**
   * Add a slider
   */
  slider(name: string, min: number, max: number, step?: number): this {
    const stepParam = step !== undefined ? `, ${step}` : '';
    this.commands.push(`${name} = Slider(${min}, ${max}${stepParam})`);
    return this;
  }

  /**
   * Get all commands
   */
  build(): string[] {
    return [...this.commands];
  }

  /**
   * Execute all commands on an API
   */
  execute(api: { evalCommand: (cmd: string) => void }): boolean {
    const safeExec = createSafeEvalCommand(this.appletType, api);

    for (const cmd of this.commands) {
      const success = safeExec.execute(cmd);
      if (!success) {
        return false;
      }
    }
    return true;
  }

  /**
   * Clear all commands
   */
  clear(): this {
    this.commands = [];
    return this;
  }
}

/**
 * Create a new command builder
 */
export function createCommandBuilder(appletType: AppletType): CommandBuilder {
  return new CommandBuilder(appletType);
}

export default {
  validateCommand,
  createSafeEvalCommand,
  getRecommendedApplet,
  buildCommand,
  parseCommand,
  CommandBuilder,
  createCommandBuilder,
};
