# SISTEMA DE INDICAÇÕES DO MOTOR E ALERTA À TRIPULAÇÃO (EICAS)

## Introdução

O sistema de indicações do motor e alerta da tripulação é uma função do sistema MDP (Processador de Displays e Missão) que fornece indicações à tripulação, como os parâmetros do motor, dados de combustível, mensagens de alerta e informações de outros sistemas. As informações são apresentadas à tripulação através do formato EICAS (Sistema de Indicações do Motor e Alerta à Tripulação) na tela do CMFD (Display Multifuncional em Cores).

A indicação visual de alarme aparece na região superior da tela do EICAS. Essa indicação são as mensagens de alerta que estão divididas em três categorias:
* **Warning**
* **Caution**
* **Advisory**

### Funcionamento e Processamento
Cada MDP possui um módulo interno dedicado às funções do EICAS que recebe os dados necessários para a geração das indicações da aeronave e mensagens de alerta. Esse módulo processa os dados e envia seus resultados para o circuito OFP (Programa de Vôo Operacional) da CPU (Unidade de Processamento Central), onde será gerada a simbologia para a placa de vídeo e, finalmente, as indicações da aeronave e as mensagens de alerta aparecem na tela EICAS do CMFD.

Em alguns casos de geração da mensagem de alerta, o próprio OFP executa o processamento, gera a simbologia e transmite as informações para a placa de vídeo, proporcionando a visualização da mensagem na tela EICAS. Os sinais usados no EICAS são provenientes de dispositivos ligados às interfaces do próprio módulo (placa) EICAS ou às outras placas do MDP. Nesse caso, os dados são transmitidos internamente para a placa EICAS.

As mensagens de warning e caution do EICAS, em sistemas essenciais da aeronave, são complementadas pelos alertas de áudio e as luzes de alerta WARN/CAUT. Sempre que ocorrer uma mensagem de warning e/ou caution, ela também é registrada na unidade VADR (Gravador de Dados e Voz). Outras funções importantes, relacionadas ao EICAS, são a detecção e o controle de desbalanceamento de combustível entre os tanques da asa, que são executadas pelo MDP em operação.

---

## Composição e Lógica de Exibição

O sistema EICAS é composto pelos MDPs, cada um dos quais possuindo uma placa EICAS, e pelos CMFDs. A tela EICAS pode ser visualizada em qualquer dos CMFDs, mas, na ocorrência de um alerta, o sistema obedece à seguinte lógica:
* Como padrão, o CMFD da direita apresentará a tela EICAS automaticamente, quando surgir a mensagem de alerta.
* Se o CMFD da esquerda já estiver exibindo a tela EICAS, ele irá exibir a mensagem de alerta.
* Se o CMFD da direita estiver fora de operação, a mensagem de alerta surgirá na tela da esquerda.
* Caso os dois CMFDs estejam desligados, a tela EICAS e a mensagem de alerta aparecerão no primeiro que for ligado.

A tela EICAS possui indicações do motor, de combustível, do sistema elétrico, do sistema hidráulico, dos compensadores das superfícies de comando, do flape, do freio aerodinâmico, da temperatura do ar externo e da altitude da cabine.

### Indicações do Motor
* Torque (formato digital e analógico).
* Ng.
* Np.
* Temperatura do óleo (formato digital e analógico).
* Pressão do óleo (formato digital e analógico).
* Regime de ajuste do motor.
* Ignição.
* Temperatura entre turbinas - T5 (formato digital e analógico).

### Indicações do Sistema de Combustível
* Fluxo de combustível.
* Quantidade inicial de combustível.
* BINGO.
* JOKER.
* Combustível remanescente (formato digital e analógico).
* Quantidade de combustível nos tanques da asa e quantidade total.

### Indicações do Sistema Elétrico
* Voltímetro (tensão do barramento de emergência).
* Amperímetro (corrente do gerador).
* Temperatura da bateria.

### Outras Indicações
* **Sistema hidráulico:** Pressão no sistema hidráulico (formato digital).
* **Compensadores das superfícies de comando:** Compensador do aileron; Compensador do leme; Compensador do profundor (analógico e digital).
* **Flape:** Posição do flape (UP/DOWN).
* **Freio aerodinâmico:** Freio aerodinâmico aberto ou fechado (open/closed).
* **Altitude da cabine:** Altitude da cabine (formato digital).

---

## Mensagens de Alerta Visual e Avisos Luminosos

As mensagens de alerta visual são exibidas no alto da tela EICAS. Tais mensagens aparecem da esquerda para a direita e cada categoria possui uma cor diferente:

* **Warning:** São exibidas na cor vermelha e representam uma condição de emergência, demandando atitude imediata da tripulação.
* **Caution:** São exibidas na cor amarela e indicam que a operação da aeronave não está correta ou falha em algum sistema. Nesse caso, as mensagens podem exigir ações imediatas ou ações corretivas da tripulação.
* **Advisory:** São exibidas na cor ciano e alertam a tripulação de que algum sistema precisa ser monitorado.

Podem ser visualizadas até dez mensagens ao mesmo tempo e, caso apareça uma nova mensagem, surgirá uma seta apontando para baixo ao lado do conjunto de mensagens. Com isso, pode-se rolar a página para visualizar as novas mensagens. As mensagens Warning sempre têm prioridade e são as primeiras a serem visualizadas, seguidas das mensagens Caution e Advisory, ou seja, sempre que surgir uma mensagem Warning, ela aparecerá na primeira posição (região superior esquerda da tela EICAS).

O sistema EICAS também ativa as luzes de alerta WARN/CAUT toda vez que surge uma mensagem Warning e/ou Caution na tela EICAS. Essas luzes estão na região superior esquerda do painel principal de instrumentos, logo acima do CMFD. Toda vez que surge uma mensagem Warning ou Caution na tela EICAS, as luzes de alerta WARN/CAUT começam a piscar, até que sejam pressionadas. A luz de alerta WARN é vermelha e a luz de alerta CAUT é âmbar. Uma vez pressionada uma luz de alerta WARN ou CAUT, a respectiva mensagem na tela do EICAS muda de caixa cheia (vídeo inverso) para caixa vazia (vídeo normal), para indicar que o alerta foi reconhecido pela tripulação. A mensagem desaparece na tela EICAS se a condição que gerou o alerta tornar-se falsa ou deixar de existir.

Complementando o sistema, existem duas indicações de alerta localizadas na região superior direita do painel principal de instrumentos:
* Luz de alerta de fogo (FIRE), a qual possui a mesma lógica da mensagem do EICAS.
* Luz de alerta do freio de estacionamento/emergência (BRAKE ON), a qual acende quando esse freio estiver acionado.

A Tabela SISTEMA DE INDICAÇÕES DO MOTOR E ALERTA À TRIPULAÇÃO (EICAS) - MENSAGENS DE ALERTA apresenta todas as mensagens de alerta do EICAS e uma breve explicação de cada mensagem.

**EFETIVIDADE:** BIPOSTO COM FLIR

---

## Tabela - MENSAGENS DE ALERTA

| REFERÊNCIA | MENSAGEM | CATEGORIA | EXPLICAÇÃO |
| :--- | :--- | :--- | :--- |
| 1 | AFT OXY | Warning | Anormalidade no regulador de oxigênio do posto traseiro |
| 2 | AP | Warning | Falha no piloto automático |
| 3 | BAT TEMP | Warning | Temperatura elevada da bateria |
| 4 | BLD LEAK | Warning | Vazamento no sistema de sangria de ar do motor |
| 5 | CAB ALT | Warning | Altitude elevada da cabine (superior a 25000ft) |
| 6 | CAB PRES | Warning | Sobrepressão na cabine |
| 7 | CHIP DET | Warning | Presença de limalhas na AGB e na RGB, ou funcionamento anormal do motor com detecção de limalhas ou na AGB ou na RGB. |
| 8 | CANOPY | Warning | Capota aberta |
| 9 | ENG MAN | Warning | Falha na PMU |
| 10 | ENG LMTS | Warning | Limites do motor alcançados |
| 11 | FIRE | Warning | Fogo detectado no motor |
| 12 | FUEL LVL | Warning | Baixo nível de combustível |
| 13 | FWD OXY | Warning | Anormalidade no regulador de oxigênio do posto dianteiro |
| 14 | LDG GEAR | Warning | Trem de pouso recolhido, quando deveria estar estendido |
| 15 | OIL PRES | Warning | Baixa/Alta pressão do óleo |
| 16 | OIL TEMP | Warning | Baixa/Alta temperatura do óleo |
| 17 | OXYGEN | Warning | Baixa pressão de saída de oxigênio do concentrador |
| 18 | AFT PIN | Caution | Pino de segurança instalado no assento do posto traseiro |
| 19 | AIR COND | Caution | Falha no condicionamento de ar |
| 20 | AP MIST | Caution | Falha na compensação do piloto automático |
| 21 | ARM OFF | Caution | A chave ARM no painel MASS/ARM do posto traseiro está na posição SAFE |
| 22 | AVIONICS | Caution | Mau funcionamento de algum equipamento aviônico |
| 23 | BATTERY | Caution | Bateria principal sendo descarregada |
| 24 | BINGO | Caution | Combustível remanescente não é suficiente para retorno à base |
| 25 | BKUP BAT | Caution | Falha no sistema da bateria de reserva |
| 26 | BLD OVHT | Caution | Sobreaquecimento no sistema de sangria de ar de motor |
| 27 | CAB ALT | Caution | Descompressão da cabine (limite de 16000ft excedido) |
| 28 | CHIP DET | Caution | Presença de limalhas na RGB com funcionamento normal do motor; ou detecção de limalhas na AGB ou na RGB com funcionamento do motor e aeronave em solo |
| 29 | ELEC XFR | Caution | Falha na transferência para a condição de emergência elétrica |
| 30 | ELEK OVH | Caution | Sobreaquecimento no compartimento eletrônico |
| 31 | EMER BRK | Caution | Baixa pressão no sistema do freio de emergência |
| 32 | EMER BUS | Caution | Barra de emergência desenergizada |
| 33 | EMER GEAR | Caution | Baixa pressão no acumulador de emergência que alimenta o trem de pouso |
| 34 | FUEL IMB | Caution | Combustível desbalanceado |
| 35 | FUEL XFER | Caution | Falha na transferência de combustível |
| 36 | FUEL FILT | Caution | Passagem secundária iminente no filtro de combustível |
| 37 | FUEL PRES | Caution | Baixa pressão do combustível |
| 38 | FUS LVL | Caution | Baixo nível de combustível no tanque da fuselagem |
| 39 | FWD PIN | Caution | Pino de segurança instalado no assento do posto dianteiro |
| 40 | GB OVLD | Caution | Sobrecarga na caixa de engrenagens |
| 41 | GEN | Caution | Gerador fora da barra |
| 42 | HYD PRES | Caution | Baixa/Alta pressão hidráulica |
| 43 | LWING LVL | Caution | Baixo nível de combustível no tanque da asa esquerda |
| 44 | MAN RUD T | Caution | A unidade de compensação automática do leme não está funcionando ou está com falha |
| 45 | PITO TAT | Caution | Falha no sistema de aquecimento primário do Pitot/TAT |
| 46 | PROP DEIC | Caution | O degelador da hélice deve ser acionado |
| 47 | RWING LVL | Caution | Baixo nivel de combustível no tanque da asa direita |
| 48 | S PITOT | Caution | Falha no sistema de aquecimento secundário do Pitot |
| 49 | STARTER | Caution | Falha no(s) contactor(es) de partida do motor |
| 50 | STORM | Caution | Aparecimento de nuvem carregada com eletricidade |
| 51 | INERT SEP | Advisory | Separação inercial ativada |
| 52 | INTC ON | Advisory | Interconexão com outra aeronave em execução |
| 53 | OXYBIT | Advisory | Autoteste do OBOGS em execução |
| 54 | XFER OVRD | Advisory | Transferência automática de combustível sobrepujada |
| 55 | WING CLOS | Advisory | Válvula de isolamento dos tanques de asa totalmente fechada |
| 56 | WS DEICE | Advisory | Degelador da capota deve ser ativado |
