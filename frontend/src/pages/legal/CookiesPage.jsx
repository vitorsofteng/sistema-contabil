import React from 'react';
import LegalLayout from './LegalLayout';

function CookiesPage({ onBack, onNavigate }) {
  return (
    <LegalLayout title="Política de Cookies" onBack={onBack} onNavigate={onNavigate} currentPage="cookies">

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">1. O que são Cookies?</h2>
        <p>
          Cookies são pequenos arquivos de texto armazenados no seu navegador quando você visita um site.
          Eles são amplamente utilizados para fazer sites funcionarem de forma eficiente, bem como para fornecer
          informações aos proprietários do site. Tecnologias similares incluem Local Storage e Session Storage.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">2. Como o Kontabil Utiliza Cookies</h2>
        <p>
          A Plataforma Kontabil utiliza cookies e tecnologias de armazenamento local de forma limitada,
          exclusivamente para o funcionamento do serviço. A seguir, detalhamos cada uso:
        </p>

        <h3 className="text-lg font-medium mt-5 mb-3">2.1 Cookies Essenciais (Estritamente Necessários)</h3>
        <p className="mb-3">
          Estes cookies são indispensáveis para o funcionamento da Plataforma e não podem ser desativados.
          Sem eles, o serviço não funciona.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-slate-50">
                <th className="text-left p-3 border border-slate-200 font-semibold">Nome</th>
                <th className="text-left p-3 border border-slate-200 font-semibold">Tipo</th>
                <th className="text-left p-3 border border-slate-200 font-semibold">Finalidade</th>
                <th className="text-left p-3 border border-slate-200 font-semibold">Duração</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="p-3 border border-slate-200 font-mono text-xs">token</td>
                <td className="p-3 border border-slate-200">Local Storage</td>
                <td className="p-3 border border-slate-200">Token de autenticação JWT — mantém o Usuário logado</td>
                <td className="p-3 border border-slate-200">Até logout ou expiração (24h)</td>
              </tr>
              <tr>
                <td className="p-3 border border-slate-200 font-mono text-xs">refresh_token</td>
                <td className="p-3 border border-slate-200">Local Storage</td>
                <td className="p-3 border border-slate-200">Token de renovação — permite manter a sessão ativa sem refazer login</td>
                <td className="p-3 border border-slate-200">Até logout ou expiração (7 dias)</td>
              </tr>
              <tr>
                <td className="p-3 border border-slate-200 font-mono text-xs">user</td>
                <td className="p-3 border border-slate-200">Local Storage</td>
                <td className="p-3 border border-slate-200">Dados básicos do Usuário logado (nome, email) para exibição na interface</td>
                <td className="p-3 border border-slate-200">Até logout</td>
              </tr>
              <tr>
                <td className="p-3 border border-slate-200 font-mono text-xs">org_id</td>
                <td className="p-3 border border-slate-200">Local Storage</td>
                <td className="p-3 border border-slate-200">Identificador da organização selecionada (multi-tenancy)</td>
                <td className="p-3 border border-slate-200">Até logout ou troca de organização</td>
              </tr>
              <tr>
                <td className="p-3 border border-slate-200 font-mono text-xs">theme</td>
                <td className="p-3 border border-slate-200">Local Storage</td>
                <td className="p-3 border border-slate-200">Preferências de tema/branding do escritório (cores, logo)</td>
                <td className="p-3 border border-slate-200">Persistente</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-lg font-medium mt-5 mb-3">2.2 Cookies de Terceiros</h3>
        <p className="mb-3">
          A Plataforma pode carregar cookies de terceiros nos seguintes casos:
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-slate-50">
                <th className="text-left p-3 border border-slate-200 font-semibold">Serviço</th>
                <th className="text-left p-3 border border-slate-200 font-semibold">Finalidade</th>
                <th className="text-left p-3 border border-slate-200 font-semibold">Categoria</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="p-3 border border-slate-200 font-medium">Stripe</td>
                <td className="p-3 border border-slate-200">Processamento seguro de pagamentos. Cookies definidos pelo Stripe durante o checkout para prevenção de fraude.</td>
                <td className="p-3 border border-slate-200">Essencial (pagamento)</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-sm text-slate-500">
          Atualmente, o Kontabil <strong>não utiliza</strong> cookies de analytics, rastreamento, publicidade
          ou redes sociais. Caso isso mude no futuro, esta política será atualizada e você será informado.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">3. Como Gerenciar Cookies</h2>
        <p>
          Você pode controlar e/ou excluir cookies através das configurações do seu navegador. A maioria dos navegadores
          permite que você:
        </p>
        <ul className="list-disc pl-6 mt-3 space-y-1">
          <li>Visualize quais cookies estão armazenados</li>
          <li>Exclua cookies individuais ou todos de uma vez</li>
          <li>Bloqueie cookies de terceiros</li>
          <li>Bloqueie todos os cookies de sites específicos</li>
          <li>Receba notificação quando um cookie está sendo definido</li>
        </ul>
        <p className="mt-3">
          <strong>Atenção:</strong> Se você bloquear os cookies essenciais do Kontabil (como o token de autenticação),
          a Plataforma não funcionará corretamente — você não conseguirá permanecer logado.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">4. O que Acontece ao Fazer Logout</h2>
        <p>
          Ao fazer logout da Plataforma, os seguintes dados são removidos do seu navegador:
        </p>
        <ul className="list-disc pl-6 mt-3 space-y-1">
          <li>Token de autenticação (acesso revogado imediatamente)</li>
          <li>Token de renovação</li>
          <li>Dados do Usuário em cache</li>
        </ul>
        <p className="mt-3">
          As preferências de tema podem ser mantidas para sua conveniência, caso retorne à Plataforma.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">5. Alterações nesta Política</h2>
        <p>
          Caso passemos a utilizar cookies adicionais (como analytics ou rastreamento), esta Política de Cookies
          será atualizada e, quando necessário, solicitaremos seu consentimento antes de ativá-los.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">6. Contato</h2>
        <p>
          Para dúvidas sobre o uso de cookies na Plataforma, entre em contato:
        </p>
        <div className="mt-3 bg-slate-50 rounded-xl p-4 text-sm">
          <p><strong>Kontabil Tecnologia Ltda.</strong></p>
          <p className="mt-1">Email: <a href="mailto:privacidade@kontabil.com.br" className="text-emerald-600 hover:underline">privacidade@kontabil.com.br</a></p>
        </div>
      </section>

    </LegalLayout>
  );
}

export default CookiesPage;
