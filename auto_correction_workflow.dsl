app:
  description: 這是一個示範「驗證與自我修正」的工作流。會透過第二個大模型來審核第一個模型的生成結果，如果不符合規定，則強制重新生成一次。
  icon: ♻️
  icon_background: '#FFEAD5'
  mode: workflow
  name: 審核與自動修正工作流 (1次重試)
kind: app
version: 0.1.2
workflow:
  environment_variables: []
  features:
    file_upload:
      image:
        enabled: false
        number_limits: 3
        transfer_methods:
        - local_file
        - remote_url
    opening_statement: ''
    retriever_resource:
      enabled: false
    sensitive_word_avoidance:
      enabled: false
    speech_to_text:
      enabled: false
    text_to_speech:
      enabled: false
      language: ''
      voice: ''
  graph:
    edges:
    - id: start-draft
      source: start
      target: draft_node
    - id: draft-verify
      source: draft_node
      target: verify_node
    - id: verify-condition
      source: verify_node
      target: if_condition
    - id: condition-success
      source: if_condition
      sourceHandle: 'true'
      target: end_success
    - id: condition-fail
      source: if_condition
      sourceHandle: 'false'
      target: retry_node
    - id: retry-end
      source: retry_node
      target: end_retry
    nodes:
    - data:
        desc: ''
        title: 開始
        type: start
        variables:
        - label: 使用者輸入
          max_length: 256
          options: []
          required: true
          type: text-input
          variable: user_input
        - label: 嚴格規定 (Rules)
          max_length: null
          options: []
          required: true
          type: paragraph
          variable: rules
      id: start
      position:
        x: 50
        y: 200
      type: custom
    - data:
        context:
          enabled: false
          variable_selector: []
        desc: ''
        model:
          completion_params:
            temperature: 0.7
          mode: chat
          name: gpt-4o-mini
          provider: openai
        prompt_template:
        - id: system_1
          role: system
          text: |
            你是一個專業的助理。請根據以下規則處理使用者的請求：
            <rules>
            {{#start.rules#}}
            </rules>
        - id: user_1
          role: user
          text: '{{#start.user_input#}}'
        title: 初稿生成 (Draft)
        type: llm
        variables: []
      id: draft_node
      position:
        x: 350
        y: 200
      type: custom
    - data:
        context:
          enabled: false
          variable_selector: []
        desc: ''
        model:
          completion_params:
            temperature: 0
          mode: chat
          name: gpt-4o-mini
          provider: openai
        prompt_template:
        - id: system_2
          role: system
          text: |
            你是一個嚴格的審查員。請檢查以下「初稿」是否完全遵守了「規則」。
            如果完全遵守，請只回答小寫的 "yes"。
            如果有任何違反，請只回答小寫的 "no"。

            <rules>
            {{#start.rules#}}
            </rules>

            <draft>
            {{#draft_node.text#}}
            </draft>
        title: 嚴格審核 (Verify)
        type: llm
        variables: []
      id: verify_node
      position:
        x: 650
        y: 200
      type: custom
    - data:
        conditions:
        - comparison_operator: contains
          id: cond_1
          value: 'yes'
          variable_selector:
          - verify_node
          - text
        desc: ''
        logical_operator: and
        title: 判斷是否合格
        type: if-else
      id: if_condition
      position:
        x: 950
        y: 200
      type: custom
    - data:
        desc: ''
        outputs:
        - value_selector:
          - draft_node
          - text
          variable: final_output
        title: 輸出成功結果
        type: end
      id: end_success
      position:
        x: 1250
        y: 50
      type: custom
    - data:
        context:
          enabled: false
          variable_selector: []
        desc: ''
        model:
          completion_params:
            temperature: 0.5
          mode: chat
          name: gpt-4o-mini
          provider: openai
        prompt_template:
        - id: system_3
          role: system
          text: |
            你先前的回答被審核為「不合格」。請重新檢視規則，並修正初稿。
            請直接輸出修正後的結果，不要包含道歉或解釋。

            <rules>
            {{#start.rules#}}
            </rules>

            <failed_draft>
            {{#draft_node.text#}}
            </failed_draft>
        title: 重新修正 (Retry)
        type: llm
        variables: []
      id: retry_node
      position:
        x: 1250
        y: 350
      type: custom
    - data:
        desc: ''
        outputs:
        - value_selector:
          - retry_node
          - text
          variable: final_output
        title: 輸出修正結果
        type: end
      id: end_retry
      position:
        x: 1550
        y: 350
      type: custom
