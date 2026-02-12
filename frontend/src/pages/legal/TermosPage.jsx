import React from 'react';
import LegalLayout from './LegalLayout';

function TermosPage({ onBack, onNavigate }) {
  return (
    <LegalLayout title="Termos de Uso" onBack={onBack} onNavigate={onNavigate} currentPage="termos">

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">1. Aceitação dos Termos</h2>
        <p>
          Ao acessar ou utilizar a plataforma Kontabil ("Plataforma"), operada por Kontabil Tecnologia Ltda. ("Kontabil", "nós"),
          você ("Usuário", "Contador") concorda integralmente com estes Termos de Uso. Caso não concorde com qualquer disposição,
          não utilize a Plataforma.
        </p>
        <p className="mt-3">
          O uso da Plataforma também está sujeito à nossa{' '}
          <button onClick={() => onNavigate('privacidade')} className="text-emerald-600 hover:underline font-medium">
            Política de Privacidade
          </button>{' '}
          e à nossa{' '}
          <button onClick={() => onNavigate('cookies')} className="text-emerald-600 hover:underline font-medium">
            Política de Cookies
          </button>.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">2. Descrição do Serviço</h2>
        <p>
          O Kontabil é uma plataforma SaaS (Software as a Service) de análise financeira voltada a contadores e escritórios
          de contabilidade. O serviço inclui, conforme o plano contratado:
        </p>
        <ul className="list-disc pl-6 mt-3 space-y-1">
          <li>Importação e organização de dados financeiros de empresas clientes</li>
          <li>Cálculo automático de indicadores financeiros (DRE, índices de liquidez, break-even, etc.)</li>
          <li>Geração de relatórios em PDF, Excel e PowerPoint</li>
          <li>Sistema de alertas inteligentes sobre a saúde financeira das empresas</li>
          <li>Parecer consultivo gerado por inteligência artificial (quando disponível)</li>
          <li>Gestão multi-empresas com isolamento de dados</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">3. Cadastro e Conta</h2>
        <p>
          Para utilizar a Plataforma, o Usuário deve criar uma conta fornecendo informações verdadeiras, completas e atualizadas.
          O Usuário é responsável por manter a confidencialidade de suas credenciais de acesso (email e senha) e por todas
          as atividades realizadas em sua conta.
        </p>
        <p className="mt-3">
          Recomendamos fortemente a ativação da autenticação de dois fatores (2FA) para maior segurança da conta.
          O Usuário deve notificar imediatamente o Kontabil em caso de uso não autorizado de sua conta.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">4. Planos e Pagamento</h2>
        <p>
          O Kontabil oferece diferentes planos de assinatura, incluindo um plano gratuito com funcionalidades limitadas.
          Os planos pagos são cobrados de forma recorrente (mensal ou anual) conforme a opção escolhida pelo Usuário.
        </p>
        <p className="mt-3">
          Os pagamentos são processados pela plataforma Stripe. O Kontabil não armazena dados completos de cartão de crédito —
          essas informações são gerenciadas exclusivamente pela Stripe conforme seus próprios termos de segurança (PCI-DSS).
        </p>
        <p className="mt-3">
          Em caso de inadimplência, o Kontabil reserva-se o direito de suspender o acesso às funcionalidades do plano contratado,
          mantendo o acesso aos dados para exportação por um período de 30 dias. Após esse prazo, os dados poderão ser excluídos.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">5. Cancelamento</h2>
        <p>
          O Usuário pode cancelar sua assinatura a qualquer momento através da Plataforma. O cancelamento terá efeito ao final
          do período de cobrança vigente, mantendo o acesso até essa data. Não há reembolso proporcional.
        </p>
        <p className="mt-3">
          O Usuário também pode solicitar a exclusão completa de sua conta e dados a qualquer momento, conforme descrito
          na Política de Privacidade (direito à exclusão — LGPD).
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">6. Uso Aceitável</h2>
        <p>O Usuário compromete-se a utilizar a Plataforma de forma ética e legal. É expressamente proibido:</p>
        <ul className="list-disc pl-6 mt-3 space-y-1">
          <li>Utilizar a Plataforma para fins ilegais, fraudulentos ou que violem a legislação brasileira</li>
          <li>Inserir dados falsos, manipulados ou que visem induzir terceiros a erro</li>
          <li>Tentar acessar dados de outros usuários ou organizações</li>
          <li>Realizar engenharia reversa, descompilar ou tentar extrair o código-fonte da Plataforma</li>
          <li>Utilizar bots, scrapers ou mecanismos automatizados para acessar a Plataforma sem autorização</li>
          <li>Sobrecarregar intencionalmente os servidores ou infraestrutura da Plataforma</li>
          <li>Revender, sublicenciar ou redistribuir o acesso à Plataforma sem autorização expressa</li>
        </ul>
        <p className="mt-3">
          O descumprimento destas regras poderá resultar na suspensão ou encerramento da conta, sem direito a reembolso.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">7. Propriedade Intelectual</h2>
        <p>
          Todo o conteúdo da Plataforma — incluindo mas não se limitando a código-fonte, design, textos, logotipos,
          algoritmos de análise, modelos de relatório e marcas — é de propriedade exclusiva do Kontabil ou de seus licenciadores,
          protegido pelas leis brasileiras de propriedade intelectual.
        </p>
        <p className="mt-3">
          Os dados financeiros inseridos pelo Usuário permanecem de propriedade do Usuário. O Kontabil não adquire
          qualquer direito sobre os dados do Usuário, exceto o direito de processá-los para prestação do serviço contratado.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">8. Inteligência Artificial</h2>
        <p>
          A Plataforma pode utilizar serviços de inteligência artificial de terceiros (Anthropic/Claude) para gerar
          pareceres consultivos financeiros. Ao utilizar esta funcionalidade:
        </p>
        <ul className="list-disc pl-6 mt-3 space-y-1">
          <li>O Usuário reconhece que indicadores financeiros da empresa analisada serão enviados à API da Anthropic para processamento</li>
          <li>Os pareceres gerados por IA são meramente informativos e não substituem a análise profissional do contador</li>
          <li>O Kontabil não se responsabiliza por decisões tomadas com base exclusiva em pareceres gerados por IA</li>
          <li>O Usuário pode optar por não utilizar esta funcionalidade a qualquer momento</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">9. Limitação de Responsabilidade</h2>
        <p>
          O Kontabil é uma ferramenta de apoio à análise financeira. Os cálculos, indicadores, alertas e relatórios
          gerados pela Plataforma são baseados nos dados fornecidos pelo Usuário e em modelos estatísticos/financeiros
          reconhecidos, mas não substituem o julgamento profissional do contador.
        </p>
        <p className="mt-3">
          O Kontabil não se responsabiliza por: (a) decisões financeiras, tributárias ou contábeis tomadas com base nos
          dados da Plataforma; (b) erros decorrentes de dados incorretos ou incompletos fornecidos pelo Usuário;
          (c) interrupções temporárias no serviço por manutenção, atualizações ou fatores fora do controle do Kontabil;
          (d) danos indiretos, incidentais ou consequenciais decorrentes do uso da Plataforma.
        </p>
        <p className="mt-3">
          Em qualquer hipótese, a responsabilidade total do Kontabil estará limitada ao valor efetivamente pago pelo
          Usuário nos 12 meses anteriores ao evento que deu causa à reclamação.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">10. Disponibilidade do Serviço</h2>
        <p>
          O Kontabil empenhará esforços razoáveis para manter a Plataforma disponível e operacional. No entanto,
          não garantimos disponibilidade ininterrupta. Manutenções programadas serão comunicadas com antecedência
          sempre que possível.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">11. Alterações nos Termos</h2>
        <p>
          O Kontabil reserva-se o direito de alterar estes Termos de Uso a qualquer momento. Alterações significativas
          serão comunicadas ao Usuário por email ou através de aviso na Plataforma. O uso continuado da Plataforma
          após a notificação constitui aceite dos novos termos.
        </p>
        <p className="mt-3">
          Quando aplicável, o Usuário poderá ser solicitado a re-aceitar os termos atualizados para continuar utilizando a Plataforma.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">12. Legislação Aplicável e Foro</h2>
        <p>
          Estes Termos de Uso são regidos pelas leis da República Federativa do Brasil. Fica eleito o foro da comarca
          da sede do Kontabil para dirimir quaisquer controvérsias decorrentes destes Termos, com renúncia de qualquer
          outro, por mais privilegiado que seja.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">13. Contato</h2>
        <p>
          Para dúvidas, sugestões ou reclamações sobre estes Termos de Uso, entre em contato conosco:
        </p>
        <div className="mt-3 bg-slate-50 rounded-xl p-4 text-sm">
          <p><strong>Kontabil Tecnologia Ltda.</strong></p>
          <p className="mt-1">Email: <a href="mailto:contato@kontabil.com.br" className="text-emerald-600 hover:underline">contato@kontabil.com.br</a></p>
          <p>Encarregado de Dados (DPO): <a href="mailto:privacidade@kontabil.com.br" className="text-emerald-600 hover:underline">privacidade@kontabil.com.br</a></p>
        </div>
      </section>

    </LegalLayout>
  );
}

export default TermosPage;
