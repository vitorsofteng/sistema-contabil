import React from 'react';
import LegalLayout from './LegalLayout';

function PrivacidadePage({ onBack, onNavigate }) {
  return (
    <LegalLayout title="Política de Privacidade" onBack={onBack} onNavigate={onNavigate} currentPage="privacidade">

      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 mb-8 text-sm text-emerald-800">
        <strong>Resumo:</strong> Coletamos apenas os dados necessários para prestar o serviço. Seus dados financeiros
        pertencem a você. Você pode exportar ou excluir seus dados a qualquer momento. Não vendemos seus dados.
      </div>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">1. Introdução</h2>
        <p>
          A Kontabil Tecnologia Ltda. ("Kontabil", "nós") leva a proteção dos seus dados pessoais a sério.
          Esta Política de Privacidade descreve como coletamos, usamos, armazenamos, compartilhamos e protegemos
          seus dados pessoais quando você utiliza nossa plataforma, em conformidade com a Lei Geral de Proteção
          de Dados Pessoais (Lei nº 13.709/2018 — LGPD) e demais normas aplicáveis.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">2. Dados Pessoais Coletados</h2>
        <p>Coletamos os seguintes tipos de dados:</p>

        <h3 className="text-lg font-medium mt-4 mb-2">2.1 Dados de Cadastro (fornecidos por você)</h3>
        <ul className="list-disc pl-6 space-y-1">
          <li>Nome completo</li>
          <li>Email</li>
          <li>Telefone / WhatsApp</li>
          <li>Nome do escritório contábil</li>
          <li>CNPJ do escritório</li>
          <li>Registro CRC (Conselho Regional de Contabilidade)</li>
          <li>Senha (armazenada apenas como hash criptográfico — nunca em texto puro)</li>
        </ul>

        <h3 className="text-lg font-medium mt-4 mb-2">2.2 Dados Financeiros das Empresas Clientes</h3>
        <ul className="list-disc pl-6 space-y-1">
          <li>Razão social, CNPJ, inscrição estadual e dados cadastrais das empresas</li>
          <li>Balancetes, dados de receita, custos, despesas e demais dados financeiros mensais</li>
          <li>Dados de balanço patrimonial (ativo, passivo, patrimônio líquido)</li>
          <li>Dados importados de sistemas contábeis (arquivos CSV, XLSX, OFX)</li>
        </ul>
        <p className="mt-3 text-sm text-slate-500">
          <strong>Importante:</strong> Esses dados são de propriedade do Usuário (contador) e de seus clientes.
          O Kontabil os processa exclusivamente para prestação do serviço contratado.
        </p>

        <h3 className="text-lg font-medium mt-4 mb-2">2.3 Dados de Uso (coletados automaticamente)</h3>
        <ul className="list-disc pl-6 space-y-1">
          <li>Endereço IP</li>
          <li>Navegador e sistema operacional (User-Agent)</li>
          <li>Data e hora de acesso</li>
          <li>Páginas visitadas e ações realizadas (logs de auditoria)</li>
          <li>Dados de sessão e autenticação</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">3. Finalidades do Tratamento</h2>
        <p>Utilizamos seus dados para as seguintes finalidades:</p>

        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-slate-50">
                <th className="text-left p-3 border border-slate-200 font-semibold">Finalidade</th>
                <th className="text-left p-3 border border-slate-200 font-semibold">Base Legal (LGPD)</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="p-3 border border-slate-200">Criar e gerenciar sua conta</td>
                <td className="p-3 border border-slate-200">Execução de contrato (Art. 7, V)</td>
              </tr>
              <tr>
                <td className="p-3 border border-slate-200">Processar dados financeiros e gerar análises</td>
                <td className="p-3 border border-slate-200">Execução de contrato (Art. 7, V)</td>
              </tr>
              <tr>
                <td className="p-3 border border-slate-200">Gerar relatórios (PDF, Excel, PPTX)</td>
                <td className="p-3 border border-slate-200">Execução de contrato (Art. 7, V)</td>
              </tr>
              <tr>
                <td className="p-3 border border-slate-200">Enviar emails transacionais (verificação, reset de senha)</td>
                <td className="p-3 border border-slate-200">Execução de contrato (Art. 7, V)</td>
              </tr>
              <tr>
                <td className="p-3 border border-slate-200">Processar pagamentos e gerenciar assinatura</td>
                <td className="p-3 border border-slate-200">Execução de contrato (Art. 7, V)</td>
              </tr>
              <tr>
                <td className="p-3 border border-slate-200">Gerar parecer consultivo por inteligência artificial</td>
                <td className="p-3 border border-slate-200">Consentimento (Art. 7, I)</td>
              </tr>
              <tr>
                <td className="p-3 border border-slate-200">Detectar atividade suspeita e proteger a conta</td>
                <td className="p-3 border border-slate-200">Legítimo interesse (Art. 7, IX)</td>
              </tr>
              <tr>
                <td className="p-3 border border-slate-200">Registro de auditoria e compliance</td>
                <td className="p-3 border border-slate-200">Obrigação legal (Art. 7, II)</td>
              </tr>
              <tr>
                <td className="p-3 border border-slate-200">Enviar comunicações de marketing e novidades</td>
                <td className="p-3 border border-slate-200">Consentimento (Art. 7, I)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">4. Compartilhamento de Dados com Terceiros</h2>
        <p>
          O Kontabil não vende, aluga ou comercializa seus dados pessoais. Compartilhamos dados apenas com os
          seguintes prestadores de serviço, estritamente para a operação da Plataforma:
        </p>

        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-slate-50">
                <th className="text-left p-3 border border-slate-200 font-semibold">Prestador</th>
                <th className="text-left p-3 border border-slate-200 font-semibold">Finalidade</th>
                <th className="text-left p-3 border border-slate-200 font-semibold">Dados Compartilhados</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="p-3 border border-slate-200 font-medium">Stripe</td>
                <td className="p-3 border border-slate-200">Processamento de pagamentos</td>
                <td className="p-3 border border-slate-200">Email, nome, dados de cobrança</td>
              </tr>
              <tr>
                <td className="p-3 border border-slate-200 font-medium">Resend</td>
                <td className="p-3 border border-slate-200">Envio de emails transacionais</td>
                <td className="p-3 border border-slate-200">Email, nome</td>
              </tr>
              <tr>
                <td className="p-3 border border-slate-200 font-medium">Anthropic (Claude)</td>
                <td className="p-3 border border-slate-200">Geração de parecer consultivo por IA</td>
                <td className="p-3 border border-slate-200">Indicadores financeiros da empresa analisada (quando o Usuário solicita parecer IA)</td>
              </tr>
              <tr>
                <td className="p-3 border border-slate-200 font-medium">Railway / Provedor de hospedagem</td>
                <td className="p-3 border border-slate-200">Infraestrutura e hospedagem da aplicação</td>
                <td className="p-3 border border-slate-200">Todos os dados são processados nos servidores do provedor</td>
              </tr>
            </tbody>
          </table>
        </div>

        <p className="mt-3 text-sm text-slate-500">
          Todos os prestadores acima possuem suas próprias políticas de privacidade e estão sujeitos a obrigações
          de proteção de dados. O compartilhamento com a Anthropic (IA) é opcional e requer consentimento específico do Usuário.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">5. Segurança dos Dados</h2>
        <p>
          Adotamos medidas técnicas e organizacionais robustas para proteger seus dados:
        </p>
        <ul className="list-disc pl-6 mt-3 space-y-1">
          <li><strong>Criptografia em trânsito:</strong> Todas as comunicações utilizam HTTPS/TLS</li>
          <li><strong>Criptografia em repouso:</strong> Dados sensíveis são criptografados com AES-256 (via Fernet/PBKDF2)</li>
          <li><strong>Senhas:</strong> Armazenadas como hash irreversível (bcrypt)</li>
          <li><strong>Autenticação:</strong> JWT com tokens de acesso de curta duração + refresh tokens</li>
          <li><strong>2FA:</strong> Autenticação de dois fatores via TOTP (Google Authenticator, Authy, etc.)</li>
          <li><strong>Rate limiting:</strong> Proteção contra ataques de força bruta</li>
          <li><strong>Auditoria:</strong> Registro de todos os acessos e ações relevantes</li>
          <li><strong>Isolamento:</strong> Multi-tenancy com isolamento de dados entre organizações</li>
          <li><strong>Headers de segurança:</strong> CSP, HSTS, X-Frame-Options e outros headers de proteção</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">6. Retenção dos Dados</h2>
        <p>Seus dados são mantidos enquanto sua conta estiver ativa. Os prazos de retenção são:</p>
        <ul className="list-disc pl-6 mt-3 space-y-1">
          <li><strong>Dados de perfil:</strong> Enquanto a conta estiver ativa, ou até exclusão solicitada pelo Usuário</li>
          <li><strong>Dados financeiros:</strong> Enquanto a conta estiver ativa, ou até exclusão solicitada pelo Usuário</li>
          <li><strong>Logs de auditoria:</strong> 90 dias após o registro, para fins de segurança</li>
          <li><strong>Dados de cobrança/faturas:</strong> 5 anos após a transação, conforme legislação fiscal brasileira</li>
          <li><strong>Backups:</strong> Até 30 dias após a exclusão dos dados originais</li>
        </ul>
        <p className="mt-3">
          Após a exclusão da conta, todos os dados pessoais e financeiros são removidos permanentemente,
          exceto aqueles cuja retenção é exigida por lei (como registros fiscais de pagamentos).
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">7. Seus Direitos (LGPD — Art. 18)</h2>
        <p>
          Como titular de dados pessoais, a LGPD garante a você os seguintes direitos, que podem ser exercidos
          a qualquer momento:
        </p>
        <ul className="list-disc pl-6 mt-3 space-y-2">
          <li>
            <strong>Confirmação e acesso:</strong> Confirmar a existência de tratamento e obter acesso aos seus dados pessoais.
            Disponível na seção "Privacidade" das configurações da sua conta.
          </li>
          <li>
            <strong>Correção:</strong> Solicitar a correção de dados incompletos, inexatos ou desatualizados.
            Disponível na edição do seu perfil.
          </li>
          <li>
            <strong>Anonimização, bloqueio ou eliminação:</strong> Solicitar a anonimização, bloqueio ou eliminação
            de dados desnecessários, excessivos ou tratados em desconformidade com a LGPD.
          </li>
          <li>
            <strong>Portabilidade:</strong> Exportar seus dados em formato legível (JSON) para outro fornecedor.
            Disponível na seção "Privacidade" das configurações da sua conta.
          </li>
          <li>
            <strong>Eliminação:</strong> Solicitar a exclusão dos dados pessoais tratados com base no consentimento.
            Disponível na seção "Privacidade" das configurações da sua conta (botão "Excluir minha conta").
          </li>
          <li>
            <strong>Informação sobre compartilhamento:</strong> Saber com quais entidades seus dados são compartilhados
            (descrito na Seção 4 desta Política).
          </li>
          <li>
            <strong>Revogação do consentimento:</strong> Revogar o consentimento dado para tratamentos opcionais
            (como parecer IA ou emails marketing), sem afetar os tratamentos anteriores.
          </li>
          <li>
            <strong>Oposição:</strong> Opor-se ao tratamento de dados quando realizado com base em legítimo interesse,
            caso entenda que há violação à LGPD.
          </li>
        </ul>
        <p className="mt-3">
          Para exercer qualquer destes direitos, utilize as funcionalidades disponíveis na Plataforma ou entre em contato
          com nosso Encarregado de Dados (DPO) pelo email{' '}
          <a href="mailto:privacidade@kontabil.com.br" className="text-emerald-600 hover:underline">privacidade@kontabil.com.br</a>.
          Responderemos em até 15 dias úteis.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">8. Transferência Internacional de Dados</h2>
        <p>
          Alguns dos nossos prestadores de serviço (como Stripe, Resend e Anthropic) podem processar dados em servidores
          localizados fora do Brasil. Nesses casos, garantimos que o tratamento atende aos requisitos da LGPD para
          transferência internacional de dados (Art. 33), incluindo a verificação de que o país destinatário proporciona
          grau adequado de proteção ou que existem garantias contratuais suficientes.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">9. Dados de Menores</h2>
        <p>
          A Plataforma é destinada exclusivamente a profissionais de contabilidade e não coleta intencionalmente
          dados de menores de 18 anos. Caso tomemos conhecimento de que dados de menores foram coletados,
          eles serão excluídos imediatamente.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">10. Alterações nesta Política</h2>
        <p>
          Esta Política de Privacidade pode ser atualizada periodicamente para refletir mudanças em nossas práticas
          ou na legislação aplicável. Alterações significativas serão comunicadas por email ou aviso na Plataforma.
          Recomendamos que você revise esta página periodicamente.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">11. Encarregado de Dados (DPO)</h2>
        <p>
          Para questões relacionadas à proteção de seus dados pessoais, entre em contato com nosso Encarregado
          de Proteção de Dados:
        </p>
        <div className="mt-3 bg-slate-50 rounded-xl p-4 text-sm">
          <p><strong>Kontabil Tecnologia Ltda.</strong></p>
          <p className="mt-1">Encarregado de Dados (DPO)</p>
          <p>Email: <a href="mailto:privacidade@kontabil.com.br" className="text-emerald-600 hover:underline">privacidade@kontabil.com.br</a></p>
        </div>
        <p className="mt-3 text-sm text-slate-500">
          Você também tem o direito de apresentar reclamação perante a Autoridade Nacional de Proteção de Dados (ANPD)
          caso entenda que o tratamento de seus dados viola a LGPD.
        </p>
      </section>

    </LegalLayout>
  );
}

export default PrivacidadePage;
