import ImportacaoAvancadaPage from './ImportacaoAvancadaPage';
import React from 'react';
import { Modal } from '../../components/ui';

function ImportUploadModal({ isOpen, onClose, empresaId, onSuccess }) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Importar Dados" size="xl">
      <ImportacaoAvancadaPage 
        empresaId={empresaId} 
        onSuccess={() => { onSuccess?.(); onClose(); }}
      />
    </Modal>
  );
}

export default ImportUploadModal;
