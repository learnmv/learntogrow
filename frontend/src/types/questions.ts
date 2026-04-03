import type { AppletType } from '../lib/geogebra-commands'

export type QuestionType = 'multiple_choice' | 'open_ended'

export interface AppletConfig {
  width?: number
  height?: number
  showToolBar?: boolean
  showAlgebraInput?: boolean
  showMenuBar?: boolean
  showAlgebraView?: boolean
}

export interface GeneratedQuestion {
  question: string
  question_type: QuestionType
  options: string[]
  answer: string
  explanation: string
  standard_code: string
  difficulty: number
  requires_diagram?: boolean
  applet_type?: AppletType
  geogebra_commands?: string[]
  applet_config?: AppletConfig
}

export interface QuestionGenerationRequest {
  standard_id: number
  difficulty?: number
  question_type?: QuestionType
  custom_prompt?: string
  model?: string
}
