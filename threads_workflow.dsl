app:
  description: 'Threads Scraper using local Playwright Docker service'
  icon: 🧵
  icon_background: '#000000'
  mode: workflow
  name: Threads Scraper (Playwright Docker)
  use_icon_as_answer_icon: false
dependencies: []
kind: app
version: 0.3.1
workflow:
  conversation_variables: []
  environment_variables: []
  features:
    file_upload:
      enabled: false
    opening_statement: ''
    retriever_resource:
      enabled: false
    sensitive_word_avoidance:
      enabled: false
    speech_to_text:
      enabled: false
    suggested_questions: []
    suggested_questions_after_answer:
      enabled: false
    text_to_speech:
      enabled: false
  graph:
    edges:
    - data:
        sourceType: start
        targetType: http-request
      id: start-to-http
      source: 'start_node'
      sourceHandle: source
      target: 'http_node'
      targetHandle: target
      type: custom
    - data:
        sourceType: http-request
        targetType: end
      id: http-to-end
      source: 'http_node'
      sourceHandle: source
      target: 'end_node'
      targetHandle: target
      type: custom
    nodes:
    - data:
        desc: '輸入搜尋關鍵字'
        title: 開始
        type: start
        variables:
        - label: search_keyword
          max_length: 100
          options: []
          required: true
          type: text-input
          variable: search_keyword
        - label: Cookies JSON (選填)
          max_length: null
          options: []
          required: false
          type: paragraph
          variable: cookies_json
      id: 'start_node'
      position:
        x: 30
        y: 200
      type: custom
    - data:
        desc: '呼叫 Docker 內部的爬蟲服務'
        title: HTTP 請求
        type: http-request
        method: POST
        url: 'http://threads-scraper:8000/scrape'
        authorization:
          type: no-auth
        headers: ''
        params: ''
        body:
          type: x-www-form-urlencoded
          data:
          - key: keyword
            type: text
            value: '{{#start_node.search_keyword#}}'
          - key: limit
            type: text
            value: '10'
          - key: cookies_str
            type: text
            value: '{{#start_node.cookies_json#}}'
        timeout:
          connect: 10
          read: 60
          write: 60
      id: 'http_node'
      position:
        x: 300
        y: 200
      type: custom
    - data:
        desc: '回傳爬取結果'
        outputs:
        - value_selector:
          - 'http_node'
          - body
          value_type: string
          variable: results
        title: 結束
        type: end
      id: 'end_node'
      position:
        x: 600
        y: 200
      type: custom
